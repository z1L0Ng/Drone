#!/usr/bin/env python3
"""Run ASR/STT plus deterministic intent parsing as a baseline.

The baseline is transcript-first: a general ASR system transcribes each 1 s
noisy command window, then a fixed rule parser maps the transcript to
emergency, movement, or unknown. This script is evaluation-only.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import numpy as np
import soundfile as sf
from scipy import signal
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 16000
DURATION_SEC = 1.0
TARGET_LEN = int(SAMPLE_RATE * DURATION_SEC)
LABELS = ("emergency", "movement", "unknown")
ACTIONABLE = {"emergency", "movement"}

# The parser is intentionally simple and deterministic. It is a naive
# transcript-to-intent baseline, not a learned model.
EMERGENCY_TERMS = {
    "abort",
    "alert",
    "backward",
    "danger",
    "emergency",
    "freeze",
    "help",
    "hold",
    "land",
    "no",
    "nope",
    "panic",
    "stop",
    "warning",
    "wow",
    "yes",
}
MOVEMENT_TERMS = {
    "back",
    "come",
    "down",
    "follow",
    "forward",
    "go",
    "left",
    "move",
    "off",
    "on",
    "right",
    "up",
}


@dataclass(frozen=True)
class Condition:
    name: str
    slug: str
    snr_db: float | None
    condition_index: int


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def abs_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover
        return f"UNAVAILABLE: {exc}"


def shell_command(argv: list[str]) -> str:
    return (
        "MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache "
        "NUMBA_DISABLE_JIT=1 KMP_DUPLICATE_LIB_OK=TRUE conda run -n drone python "
        + " ".join(shlex.quote(part) for part in argv)
    )


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)


def require_dir(path: Path) -> None:
    if not path.is_dir():
        raise FileNotFoundError(path)


def json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
        f.write("\n")


def load_condition(manifest_path: Path, condition_slug: str) -> tuple[dict[str, Any], Condition]:
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    conditions = manifest.get("mixing", {}).get("conditions", [])
    for idx, raw in enumerate(conditions):
        if raw.get("slug") == condition_slug:
            return manifest, Condition(
                name=str(raw.get("name")),
                slug=str(raw.get("slug")),
                snr_db=raw.get("snr_db"),
                condition_index=idx,
            )
    raise RuntimeError(f"Condition slug {condition_slug!r} not found in {manifest_path}")


def load_audio_1s(path: Path) -> np.ndarray:
    y, sr = sf.read(str(path), dtype="float32")
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    if sr != SAMPLE_RATE:
        gcd = int(np.gcd(sr, SAMPLE_RATE))
        y = signal.resample_poly(y, SAMPLE_RATE // gcd, sr // gcd).astype(np.float32)
    if len(y) < TARGET_LEN:
        y = np.pad(y, (0, TARGET_LEN - len(y)), mode="constant")
    elif len(y) > TARGET_LEN:
        y = y[:TARGET_LEN]
    return np.asarray(y, dtype=np.float32)


def list_noise_files(noise_dir: Path) -> list[Path]:
    files = sorted(p for p in noise_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".wav", ".flac", ".ogg", ".mp3"})
    if not files:
        raise RuntimeError(f"No noise audio files under {noise_dir}")
    return files


def load_noise_bank(noise_files: list[Path]) -> list[np.ndarray]:
    bank = []
    for path in noise_files:
        y = load_audio_1s(path)
        if float(np.mean(np.square(y), dtype=np.float64)) <= 1e-12:
            raise RuntimeError(f"Noise file has near-zero power: {path}")
        bank.append(y)
    return bank


def deterministic_noise(noise_bank: list[np.ndarray], seed: int, cond_index: int, sample_index: int) -> np.ndarray:
    seq = np.random.SeedSequence([int(seed), int(cond_index), int(sample_index)])
    rng = np.random.default_rng(seq)
    noise = noise_bank[int(rng.integers(0, len(noise_bank)))]
    if len(noise) == TARGET_LEN:
        return noise
    if len(noise) < TARGET_LEN:
        return np.resize(noise, TARGET_LEN).astype(np.float32)
    start = int(rng.integers(0, len(noise) - TARGET_LEN + 1))
    return noise[start:start + TARGET_LEN].astype(np.float32)


def mix_at_snr(clean: np.ndarray, noise: np.ndarray, snr_db: float) -> tuple[np.ndarray, bool, float]:
    speech_power = float(np.mean(np.square(clean), dtype=np.float64))
    noise_power = float(np.mean(np.square(noise), dtype=np.float64))
    if speech_power <= 1e-12:
        raise RuntimeError("Near-zero-power speech sample")
    if noise_power <= 1e-12:
        raise RuntimeError("Near-zero-power noise sample")
    target_noise_power = speech_power / float(10.0 ** (snr_db / 10.0))
    noise_scale = float(np.sqrt(target_noise_power / noise_power))
    mixed = clean + noise * noise_scale
    peak = float(np.max(np.abs(mixed))) if mixed.size else 0.0
    normalized = False
    if peak > 1.0:
        mixed = mixed / peak
        normalized = True
    return mixed.astype(np.float32), normalized, peak


def load_test_split(processed_path: Path, limit: int | None) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(str(processed_path), allow_pickle=True)
    x_paths = np.asarray(data["X_test"])
    y_true = np.asarray(data["y_test"], dtype=np.int64)
    if limit is not None:
        x_paths = x_paths[:limit]
        y_true = y_true[:limit]
    resolved = np.array([str(abs_path(str(p))) for p in x_paths], dtype=object)
    missing = [p for p in resolved if not Path(str(p)).is_file()]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} test files; first={missing[0]}")
    return resolved, y_true


def label_name(idx: int) -> str:
    return LABELS[int(idx)]


def source_word(path: str) -> str:
    parts = Path(path).parts
    try:
        raw_i = parts.index("raw")
        return parts[raw_i + 2]
    except Exception:
        return ""


def normalize_transcript(text: str) -> tuple[str, list[str]]:
    norm = re.sub(r"[^a-zA-Z]+", " ", str(text).lower()).strip()
    tokens = [tok for tok in norm.split() if tok]
    return norm, tokens


def parse_intent(tokens: list[str]) -> tuple[str, list[str], list[str], str]:
    token_set = set(tokens)
    emergency_hits = sorted(token_set & EMERGENCY_TERMS)
    movement_hits = sorted(token_set & MOVEMENT_TERMS)
    if emergency_hits:
        return "emergency", emergency_hits, movement_hits, "emergency_precedence"
    if movement_hits:
        return "movement", emergency_hits, movement_hits, "movement_match"
    return "unknown", emergency_hits, movement_hits, "no_rule_hit"


class WhisperAsr:
    def __init__(self, model_name: str, device: str, model_cache_dir: Path, torch_num_threads: int | None) -> None:
        import torch
        import whisper

        if torch_num_threads is not None and int(torch_num_threads) > 0:
            torch.set_num_threads(int(torch_num_threads))
        if device == "auto":
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        self.system = "whisper"
        self.model_name = model_name
        self.device = device
        self.cache_dir = model_cache_dir
        model_cache_dir.mkdir(parents=True, exist_ok=True)
        self.model = whisper.load_model(model_name, device=device, download_root=str(model_cache_dir))

    def transcribe(self, audio: np.ndarray) -> str:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = self.model.transcribe(
                audio.astype(np.float32),
                language="en",
                task="transcribe",
                fp16=False,
                temperature=0.0,
                condition_on_previous_text=False,
                verbose=False,
            )
        return str(result.get("text", "")).strip()


def cache_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return int(path.stat().st_size)
    return int(sum(p.stat().st_size for p in path.rglob("*") if p.is_file()))


def write_startup_receipt(
    output_dir: Path,
    args: argparse.Namespace,
    condition: Condition,
    processed_path: Path,
    noise_dir: Path,
    model_cache_dir: Path,
) -> None:
    text = f"""# Startup Receipt

- timestamp: `{datetime.now().isoformat(timespec="seconds")}`
- commit_sha: `{run_git(["rev-parse", "HEAD"])}`
- git_branch: `{run_git(["branch", "--show-current"])}`
- exact_command: `{shell_command(sys.argv)}`
- python_executable: `{sys.executable}`
- python_version: `{sys.version.split()[0]}`
- asr_system: `{args.asr_system}`
- asr_model: `{args.model_name}`
- asr_device: `{args.device}`
- model_cache_dir: `{rel(model_cache_dir)}`
- input_split: `{rel(processed_path)}`
- noise_manifest: `{rel(abs_path(args.noise_manifest))}`
- noise_source: `{rel(noise_dir)}`
- noise_condition: `{condition.slug}` / `{condition.snr_db}` dB
- output_directory: `{rel(output_dir)}`
"""
    (output_dir / "startup_receipt.md").write_text(text, encoding="utf-8")


def write_result_tree(output_dir: Path) -> None:
    lines = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            lines.append(f"{rel(path)}\t{path.stat().st_size} bytes")
    (output_dir / "result_tree.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_confusion_matrix(path: Path, cm: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["true\\pred", *LABELS])
        for idx, row in enumerate(cm):
            writer.writerow([LABELS[idx], *[int(x) for x in row]])


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.quantile(np.asarray(values, dtype=np.float64), q))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asr-system", default="whisper", choices=["whisper"])
    parser.add_argument("--model-name", default="tiny.en")
    parser.add_argument("--processed-data-path", default="dataset/processed/data_paths.npz")
    parser.add_argument("--noise-manifest", default="weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603/run_manifest.json")
    parser.add_argument("--condition-slug", default="snr_m10db")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-cache-dir", default="weeklyresult/weekly_drone_2026w23/asr_stt_model_cache/whisper")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--device", default="cpu", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--torch-num-threads", type=int, default=None)
    parser.add_argument("--progress-every", type=int, default=25)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = abs_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    processed_path = abs_path(args.processed_data_path)
    manifest_path = abs_path(args.noise_manifest)
    model_cache_dir = abs_path(args.model_cache_dir)
    require_file(processed_path)
    require_file(manifest_path)
    manifest, condition = load_condition(manifest_path, args.condition_slug)
    noise_dir = abs_path(manifest["noise"]["source_dir"])
    require_dir(noise_dir)

    write_startup_receipt(output_dir, args, condition, processed_path, noise_dir, model_cache_dir)

    seed = int(manifest["mixing"]["seed"])
    x_paths, y_true = load_test_split(processed_path, args.limit)
    noise_files = list_noise_files(noise_dir)
    noise_bank = load_noise_bank(noise_files)

    load_start = time.perf_counter()
    if args.asr_system == "whisper":
        asr = WhisperAsr(args.model_name, args.device, model_cache_dir, args.torch_num_threads)
    else:  # pragma: no cover
        raise RuntimeError(f"Unsupported ASR system: {args.asr_system}")
    model_load_sec = time.perf_counter() - load_start

    transcript_rows: list[dict[str, Any]] = []
    parsed_rows: list[dict[str, Any]] = []
    y_pred: list[int] = []
    y_eval_true: list[int] = []
    asr_latencies: list[float] = []
    total_latencies: list[float] = []
    failures = 0
    skipped = 0
    peak_normalized = 0

    start_all = time.perf_counter()
    for sample_i, path_raw in enumerate(x_paths):
        true_idx = int(y_true[sample_i])
        true_label = label_name(true_idx)
        path = Path(str(path_raw))
        sample_start = time.perf_counter()
        transcript = ""
        error = ""
        asr_failed = False
        try:
            clean = load_audio_1s(path)
            if condition.snr_db is None:
                audio = clean
                normalized = False
                peak = float(np.max(np.abs(audio))) if audio.size else 0.0
            else:
                noise = deterministic_noise(noise_bank, seed, condition.condition_index, sample_i)
                audio, normalized, peak = mix_at_snr(clean, noise, float(condition.snr_db))
            if normalized:
                peak_normalized += 1
            asr_start = time.perf_counter()
            transcript = asr.transcribe(audio)
            asr_latency = time.perf_counter() - asr_start
        except Exception as exc:
            failures += 1
            asr_failed = True
            asr_latency = 0.0
            error = repr(exc)

        total_latency = time.perf_counter() - sample_start
        norm, tokens = normalize_transcript(transcript)
        pred_label, emergency_hits, movement_hits, parse_reason = parse_intent(tokens)
        pred_idx = LABELS.index(pred_label)
        keyword_hit = bool(emergency_hits or movement_hits)

        if not asr_failed:
            y_eval_true.append(true_idx)
            y_pred.append(pred_idx)
            asr_latencies.append(float(asr_latency))
            total_latencies.append(float(total_latency))
        else:
            skipped += 1

        transcript_rows.append(
            {
                "sample_index": sample_i,
                "filepath": rel(path),
                "source_word": source_word(str(path)),
                "true_label": true_label,
                "condition": condition.slug,
                "snr_db": "" if condition.snr_db is None else condition.snr_db,
                "transcript_raw": transcript,
                "transcript_normalized": norm,
                "transcript_non_empty": int(bool(tokens)),
                "asr_latency_sec": f"{asr_latency:.6f}",
                "total_latency_sec": f"{total_latency:.6f}",
                "peak_normalized": int(False if asr_failed else normalized),
                "peak_before_normalization": "" if asr_failed else f"{peak:.6f}",
                "asr_failed": int(asr_failed),
                "error": error,
            }
        )
        parsed_rows.append(
            {
                "sample_index": sample_i,
                "true_label": true_label,
                "predicted_intent": pred_label,
                "is_correct": int((not asr_failed) and pred_idx == true_idx),
                "keyword_hit": int(keyword_hit),
                "matched_emergency_terms": " ".join(emergency_hits),
                "matched_movement_terms": " ".join(movement_hits),
                "parse_reason": parse_reason if not asr_failed else "asr_failed",
                "false_action_from_unknown": int((not asr_failed) and true_label == "unknown" and pred_label in ACTIONABLE),
                "asr_failed": int(asr_failed),
            }
        )

        if (sample_i + 1) % max(1, int(args.progress_every)) == 0 or sample_i + 1 == len(x_paths):
            elapsed = time.perf_counter() - start_all
            print(f"[eval] {sample_i + 1}/{len(x_paths)} elapsed={elapsed:.1f}s failures={failures}", flush=True)

    y_eval_true_arr = np.asarray(y_eval_true, dtype=np.int64)
    y_pred_arr = np.asarray(y_pred, dtype=np.int64)
    if len(y_eval_true_arr) == 0:
        raise RuntimeError("No successfully evaluated samples")

    cm = confusion_matrix(y_eval_true_arr, y_pred_arr, labels=np.arange(len(LABELS)))
    report_text = classification_report(y_eval_true_arr, y_pred_arr, labels=np.arange(len(LABELS)), target_names=LABELS, digits=4, zero_division=0)
    report_dict = classification_report(y_eval_true_arr, y_pred_arr, labels=np.arange(len(LABELS)), target_names=LABELS, output_dict=True, zero_division=0)

    n_total = len(x_paths)
    n_success = len(y_eval_true_arr)
    transcript_non_empty = sum(int(row["transcript_non_empty"]) for row in transcript_rows if not int(row["asr_failed"]))
    keyword_hits = sum(int(row["keyword_hit"]) for row in parsed_rows if not int(row["asr_failed"]))
    unknown_idx = LABELS.index("unknown")
    unknown_mask = y_eval_true_arr == unknown_idx
    unknown_false_actions = int(np.sum(np.isin(y_pred_arr[unknown_mask], [LABELS.index("emergency"), LABELS.index("movement")])))
    n_unknown = int(np.sum(unknown_mask))
    metrics = {
        "asr_system": args.asr_system,
        "asr_model": args.model_name,
        "asr_device": asr.device,
        "condition": condition.slug,
        "snr_db": condition.snr_db,
        "n_total": int(n_total),
        "n_success": int(n_success),
        "transcript_count": int(n_success),
        "parsed_count": int(n_success),
        "skipped_failed_files": int(skipped),
        "transcript_non_empty_rate": float(transcript_non_empty / n_success),
        "keyword_hit_rate": float(keyword_hits / n_success),
        "intent_parse_accuracy": float(accuracy_score(y_eval_true_arr, y_pred_arr)),
        "intent_parse_macro_f1": float(f1_score(y_eval_true_arr, y_pred_arr, average="macro", zero_division=0)),
        "emergency_recall": float(report_dict["emergency"]["recall"]),
        "unknown_false_action_rate": float(unknown_false_actions / n_unknown) if n_unknown else 0.0,
        "parse_failure_rate": float(skipped / n_total),
        "no_rule_hit_rate": float(sum(1 for row in parsed_rows if row["parse_reason"] == "no_rule_hit") / n_success),
        "model_load_sec": float(model_load_sec),
        "model_cache_size_bytes": cache_size_bytes(model_cache_dir),
        "peak_normalized_count": int(peak_normalized),
        "peak_normalized_fraction": float(peak_normalized / n_success),
        "deployment_caveat": "Whisper tiny.en is a transcript-first ASR baseline; it is not an MCU-deployable intent-event recognizer and requires PyTorch-class runtime.",
        "classification_report": report_dict,
    }
    latency_summary = {
        "asr_latency_sec": {
            "median": quantile(asr_latencies, 0.50),
            "p95": quantile(asr_latencies, 0.95),
            "mean": float(np.mean(asr_latencies)) if asr_latencies else None,
        },
        "total_per_sample_latency_sec": {
            "median": quantile(total_latencies, 0.50),
            "p95": quantile(total_latencies, 0.95),
            "mean": float(np.mean(total_latencies)) if total_latencies else None,
        },
        "model_load_sec": float(model_load_sec),
        "total_run_sec": float(time.perf_counter() - start_all),
        "realtime_factor_asr_median": quantile(asr_latencies, 0.50) / DURATION_SEC if asr_latencies else None,
        "realtime_factor_total_median": quantile(total_latencies, 0.50) / DURATION_SEC if total_latencies else None,
    }

    write_csv(
        output_dir / "transcripts.csv",
        transcript_rows,
        [
            "sample_index",
            "filepath",
            "source_word",
            "true_label",
            "condition",
            "snr_db",
            "transcript_raw",
            "transcript_normalized",
            "transcript_non_empty",
            "asr_latency_sec",
            "total_latency_sec",
            "peak_normalized",
            "peak_before_normalization",
            "asr_failed",
            "error",
        ],
    )
    write_csv(
        output_dir / "parsed_intents.csv",
        parsed_rows,
        [
            "sample_index",
            "true_label",
            "predicted_intent",
            "is_correct",
            "keyword_hit",
            "matched_emergency_terms",
            "matched_movement_terms",
            "parse_reason",
            "false_action_from_unknown",
            "asr_failed",
        ],
    )
    (output_dir / "classification_report_intent_parse.txt").write_text(report_text, encoding="utf-8")
    write_confusion_matrix(output_dir / "confusion_matrix_intent_parse.csv", cm)
    json_dump(output_dir / "metrics.json", metrics)
    json_dump(output_dir / "latency_summary.json", latency_summary)

    run_manifest = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "git": {
            "branch": run_git(["branch", "--show-current"]),
            "head": run_git(["rev-parse", "HEAD"]),
            "status_short_branch": run_git(["status", "--short", "--branch"]).splitlines(),
        },
        "command": {
            "argv": sys.argv,
            "shell_command": shell_command(sys.argv),
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
        "asr": {
            "system": args.asr_system,
            "model_name": args.model_name,
            "device": asr.device,
            "model_cache_dir": rel(model_cache_dir),
            "model_cache_size_bytes": cache_size_bytes(model_cache_dir),
        },
        "parser": {
            "precedence": "emergency > movement > unknown",
            "emergency_terms": sorted(EMERGENCY_TERMS),
            "movement_terms": sorted(MOVEMENT_TERMS),
            "unknown_rule": "fallback when no emergency or movement term is matched",
        },
        "input": {
            "processed_data_path": rel(processed_path),
            "test_split": "X_test/y_test",
            "limit": args.limit,
            "noise_manifest": rel(manifest_path),
            "noise_source_dir": rel(noise_dir),
            "condition": {
                "name": condition.name,
                "slug": condition.slug,
                "snr_db": condition.snr_db,
                "condition_index": condition.condition_index,
            },
            "seed": seed,
            "mixing_formula": manifest["mixing"]["snr_formula"],
            "clipping_rule": manifest["mixing"]["clipping_rule"],
        },
        "outputs": {
            "startup_receipt": rel(output_dir / "startup_receipt.md"),
            "run_manifest": rel(output_dir / "run_manifest.json"),
            "transcripts": rel(output_dir / "transcripts.csv"),
            "parsed_intents": rel(output_dir / "parsed_intents.csv"),
            "metrics": rel(output_dir / "metrics.json"),
            "classification_report": rel(output_dir / "classification_report_intent_parse.txt"),
            "confusion_matrix": rel(output_dir / "confusion_matrix_intent_parse.csv"),
            "latency_summary": rel(output_dir / "latency_summary.json"),
            "report": rel(output_dir / "report.md"),
            "result_tree": rel(output_dir / "result_tree.txt"),
        },
    }
    json_dump(output_dir / "run_manifest.json", run_manifest)

    report = f"""# ASR/STT Intent Parser Baseline

Status: {'SMOKE' if args.limit else 'FULL'} local evaluation.

## Runtime Summary

- ASR system/model: `{args.asr_system}` / `{args.model_name}`
- Device: `{asr.device}`
- Condition: `{condition.slug}` (`{condition.snr_db}` dB)
- Total samples requested: `{n_total}`
- Transcript count: `{n_success}`
- Parsed count: `{n_success}`
- Skipped/failed files: `{skipped}`
- Total run time: `{latency_summary['total_run_sec']:.2f}` s
- Median/p95 ASR latency: `{latency_summary['asr_latency_sec']['median']:.4f}` / `{latency_summary['asr_latency_sec']['p95']:.4f}` s
- Model cache size: `{metrics['model_cache_size_bytes']}` bytes

## Metric Summary

- transcript non-empty rate: `{metrics['transcript_non_empty_rate']:.4f}`
- keyword hit rate: `{metrics['keyword_hit_rate']:.4f}`
- intent parse accuracy: `{metrics['intent_parse_accuracy']:.4f}`
- intent parse macro F1: `{metrics['intent_parse_macro_f1']:.4f}`
- emergency recall: `{metrics['emergency_recall']:.4f}`
- unknown false action rate: `{metrics['unknown_false_action_rate']:.4f}`
- parse failure rate: `{metrics['parse_failure_rate']:.4f}`

## Deployment Caveat

{metrics['deployment_caveat']}

## Result Tree

See `result_tree.txt`.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    write_result_tree(output_dir)
    print(f"[done] wrote {rel(output_dir)}", flush=True)
    print(json.dumps({k: metrics[k] for k in [
        "n_total",
        "n_success",
        "intent_parse_accuracy",
        "intent_parse_macro_f1",
        "emergency_recall",
        "unknown_false_action_rate",
        "transcript_non_empty_rate",
        "keyword_hit_rate",
        "parse_failure_rate",
    ]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
