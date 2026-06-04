#!/usr/bin/env python3
"""Re-run ESP32 candidate TFLite inference on user-study SD WAV files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import wave
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
HOST_DIR = REPO_ROOT / "realworld" / "esp32" / "host"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(HOST_DIR) not in sys.path:
    sys.path.insert(0, str(HOST_DIR))

from logmel_frontend_shared import ensure_target_len, extract_logmel_input  # noqa: E402


INPUT_ROOT = Path("/Users/zilongzeng/Research/DroneControl/user_study_v1")
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "weeklyresult"
    / "weekly_drone_2026w23"
    / "user_study_v1_esp32_candidate_reinfer_20260604_025517"
)
DEFAULT_TFLITE = (
    REPO_ROOT
    / "weeklyresult"
    / "weekly_drone_2026w19"
    / "realworld"
    / "esp32_rt1s_c32_validation"
    / "xiao_rt1s_c32_b256_samearch_ts_full_integer.tflite"
)
DEFAULT_MODEL_TEST_INFO = (
    REPO_ROOT
    / "weeklyresult"
    / "weekly_drone_2026w19"
    / "realworld"
    / "esp32_rt1s_c32_validation"
    / "MODEL_TEST_INFO.json"
)
DEFAULT_TFLM_PRECHECK = (
    REPO_ROOT
    / "weeklyresult"
    / "weekly_drone_2026w19"
    / "realworld"
    / "esp32_rt1s_c32_validation"
    / "tflm_candidate_precheck.json"
)
DEFAULT_RUN_CONFIG = (
    REPO_ROOT / "weeklyresult" / "weekly_drone_2026w19" / "xiao_rt1s_c32_b256_samearch_ts" / "run_config.json"
)
DEFAULT_FIRMWARE_CONFIG = REPO_ROOT / "realworld" / "esp32" / "firmware" / "esp32_user_study_cdc_sd_logger" / "config.h"
DEFAULT_FRONTEND_CONFIG = REPO_ROOT / "src" / "model_config.py"
DEFAULT_FRONTEND_SHARED = REPO_ROOT / "src" / "logmel_frontend_shared.py"
DEFAULT_FRONTEND_CONSTANTS = REPO_ROOT / "realworld" / "esp32" / "firmware" / "esp32_local_cdc" / "frontend_constants.h"
DEFAULT_LABEL_ENCODER = REPO_ROOT / "saved_models" / "label_encoder.joblib"
DEFAULT_EXTERNAL_BOARD_LOG_ROOT = REPO_ROOT / "weeklyresult" / "weekly_drone_2026w20" / "realworld"
CLASS_ORDER = ["emergency", "movement", "unknown"]
INTENT_DIR_MAP = {"emergency": "emergency", "movement": "movement", "unknown": "unknown"}
LEGACY_KEYWORD_INTENT_MAP = {
    "abort": "emergency",
    "freeze": "emergency",
    "help": "emergency",
    "hold": "emergency",
    "stop": "emergency",
    "down": "movement",
    "follow": "movement",
    "forward": "movement",
    "go": "movement",
    "left": "movement",
    "right": "movement",
    "up": "movement",
    "bed": "unknown",
    "bird": "unknown",
    "cat": "unknown",
    "dog": "unknown",
    "happy": "unknown",
    "no": "unknown",
    "one": "unknown",
    "two": "unknown",
    "wow": "unknown",
    "yes": "unknown",
}
BOARD_TIMING_FIELDS = ["capture_ms", "frontend_ms", "infer_ms", "total_ms"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dataset-name", default="user_study_v1")
    parser.add_argument("--mode", choices=["smoke", "full"], default="full")
    parser.add_argument("--smoke-per-intent", type=int, default=2)
    parser.add_argument("--tflite", type=Path, default=DEFAULT_TFLITE)
    parser.add_argument("--label-encoder", type=Path, default=DEFAULT_LABEL_ENCODER)
    parser.add_argument("--candidate-name", default="xiao_rt1s_c32_b256_samearch_ts")
    parser.add_argument("--model-test-info", type=Path, default=DEFAULT_MODEL_TEST_INFO)
    parser.add_argument("--tflm-precheck", type=Path, default=DEFAULT_TFLM_PRECHECK)
    parser.add_argument("--run-config", type=Path, default=DEFAULT_RUN_CONFIG)
    parser.add_argument("--firmware-config", type=Path, default=DEFAULT_FIRMWARE_CONFIG)
    parser.add_argument("--frontend-config", type=Path, default=DEFAULT_FRONTEND_CONFIG)
    parser.add_argument("--frontend-shared", type=Path, default=DEFAULT_FRONTEND_SHARED)
    parser.add_argument("--frontend-constants", type=Path, default=DEFAULT_FRONTEND_CONSTANTS)
    parser.add_argument("--external-board-log-root", type=Path, default=DEFAULT_EXTERNAL_BOARD_LOG_ROOT)
    return parser.parse_args()


def run_git(args: list[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT)
        return out.strip()
    except subprocess.CalledProcessError as exc:
        return exc.output.strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_intent(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def numeric_sort_key(path: Path) -> tuple[int, Any, str]:
    try:
        return (0, int(path.stem), str(path))
    except ValueError:
        return (1, path.name, str(path))


def inspect_wav(path: Path) -> tuple[dict[str, Any], str]:
    try:
        with wave.open(str(path), "rb") as w:
            info = {
                "channels": int(w.getnchannels()),
                "sample_width_bytes": int(w.getsampwidth()),
                "sample_rate_hz": int(w.getframerate()),
                "frames": int(w.getnframes()),
                "duration_sec": float(w.getnframes()) / float(w.getframerate() or 1),
                "comptype": w.getcomptype(),
            }
        reason = ""
        if info["channels"] != 1:
            reason = "not_mono"
        elif info["sample_width_bytes"] != 2:
            reason = "not_pcm16"
        elif info["sample_rate_hz"] != 16000:
            reason = "not_16khz"
        return info, reason
    except Exception as exc:  # noqa: BLE001
        return {}, f"wav_decode_error:{exc}"


def add_wav_trials(
    trials: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    input_root: Path,
    participant_dir: Path,
    search_dir: Path,
    intent: str,
    keyword: str | None,
    label_source: str,
) -> None:
    wavs = sorted(search_dir.rglob("*.wav"), key=numeric_sort_key)
    for wav_path in wavs:
        rel_parts = wav_path.relative_to(input_root).parts
        observed_keyword = keyword or "unavailable_in_sd_path"
        if keyword is None and len(rel_parts) >= 4:
            observed_keyword = rel_parts[2]
        try:
            repeat_idx: int | str = int(wav_path.stem)
        except ValueError:
            repeat_idx = wav_path.stem
        info, reason = inspect_wav(wav_path)
        base = {
            "participant_id": participant_dir.name,
            "intent_ground_truth": intent,
            "keyword": observed_keyword,
            "repeat_idx": repeat_idx,
            "audio_path": str(wav_path.resolve()),
            "audio_relpath": str(wav_path.relative_to(input_root)),
            "audio_format": info,
            "label_source": label_source,
        }
        if reason:
            skipped.append({**base, "reason": reason})
        else:
            trials.append(base)


def scan_trials(input_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    participants = sorted([p for p in input_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
    for participant_dir in participants:
        for label_dir in sorted([p for p in participant_dir.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
            label_name = normalize_intent(label_dir.name)
            if label_name in CLASS_ORDER:
                add_wav_trials(
                    trials,
                    skipped,
                    input_root,
                    participant_dir,
                    label_dir,
                    label_name,
                    None,
                    "intent_directory",
                )
            elif label_name in LEGACY_KEYWORD_INTENT_MAP:
                add_wav_trials(
                    trials,
                    skipped,
                    input_root,
                    participant_dir,
                    label_dir,
                    LEGACY_KEYWORD_INTENT_MAP[label_name],
                    label_name,
                    "legacy_keyword_mapping",
                )
            else:
                skipped.append(
                    {
                        "audio_path": str(label_dir),
                        "participant_id": participant_dir.name,
                        "intent_ground_truth": label_name,
                        "reason": "unknown_intent_or_keyword_directory",
                    }
                )
    return trials, skipped, build_data_audit(input_root, trials, skipped)


def build_data_audit(input_root: Path, trials: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> dict[str, Any]:
    participants = sorted({row["participant_id"] for row in trials} | {row.get("participant_id", "") for row in skipped if row.get("participant_id")})
    count_by_participant_intent: dict[str, dict[str, int]] = {}
    format_counts: Counter[str] = Counter()
    frame_counts: Counter[str] = Counter()
    label_source_counts: Counter[str] = Counter()
    for row in trials:
        participant = row["participant_id"]
        intent = row["intent_ground_truth"]
        count_by_participant_intent.setdefault(participant, {c: 0 for c in CLASS_ORDER})
        count_by_participant_intent[participant][intent] += 1
        label_source_counts[str(row.get("label_source", "unknown"))] += 1
        fmt = row.get("audio_format", {})
        format_counts[
            json.dumps(
                {
                    "channels": fmt.get("channels"),
                    "sample_width_bytes": fmt.get("sample_width_bytes"),
                    "sample_rate_hz": fmt.get("sample_rate_hz"),
                },
                sort_keys=True,
            )
        ] += 1
        frame_counts[str(fmt.get("frames", ""))] += 1

    missing_expected: list[dict[str, Any]] = []
    for participant in participants:
        by_intent = count_by_participant_intent.get(participant, {c: 0 for c in CLASS_ORDER})
        for intent in CLASS_ORDER:
            seen = by_intent.get(intent, 0)
            if seen != 50:
                missing_expected.append(
                    {
                        "participant_id": participant,
                        "intent": intent,
                        "expected_files_if_full_50": 50,
                        "observed_files": seen,
                        "missing_count": max(50 - seen, 0),
                        "extra_count": max(seen - 50, 0),
                        "delta_observed_minus_expected": seen - 50,
                    }
                )

    observed_structures = []
    if label_source_counts.get("intent_directory"):
        observed_structures.append("participant/intent/keyword/*.wav")
    if label_source_counts.get("legacy_keyword_mapping"):
        observed_structures.append("participant/keyword/*.wav")

    return {
        "input_root": str(input_root.resolve()),
        "participants": participants,
        "participant_count": len(participants),
        "valid_trial_count": len(trials),
        "skipped_count": len(skipped),
        "count_by_participant_intent": count_by_participant_intent,
        "label_source_counts": dict(label_source_counts),
        "observed_structures": observed_structures,
        "audio_format_counts": dict(format_counts),
        "frame_count_distribution": dict(sorted(frame_counts.items(), key=lambda x: (int(x[0]) if x[0].isdigit() else -1))),
        "expected_full_intent_grid_trials": len(participants) * len(CLASS_ORDER) * 50,
        "missing_against_full_50_per_intent": missing_expected,
        "missing_file_count_against_modern_full_50": sum(int(r["missing_count"]) for r in missing_expected),
        "extra_file_count_against_modern_full_50": sum(int(r["extra_count"]) for r in missing_expected),
        "keyword_encoded_in_sd_path": any(row["keyword"] != "unavailable_in_sd_path" for row in trials),
        "legacy_keyword_mapping_used": bool(label_source_counts.get("legacy_keyword_mapping")),
        "legacy_keyword_mapping": LEGACY_KEYWORD_INTENT_MAP if label_source_counts.get("legacy_keyword_mapping") else {},
        "input_results_csv_count": len(list(input_root.rglob("results.csv"))),
        "board_logs_inside_input_root": bool(list(input_root.rglob("*.csv")) or list(input_root.rglob("*.json"))),
    }


def board_log_key(participant: str, intent: str, keyword: str, wav_filename: str) -> tuple[str, str, str, str]:
    return (
        participant.strip().lower(),
        normalize_intent(intent),
        normalize_intent(keyword),
        wav_filename.strip(),
    )


def load_input_board_logs(input_root: Path) -> tuple[dict[tuple[str, str, str, str], dict[str, Any]], dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    joined_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    duplicate_keys: list[dict[str, Any]] = []
    all_fields: set[str] = set()
    row_count = 0
    rows_with_prediction = 0
    rows_with_timing = 0
    for path in sorted(input_root.rglob("results.csv")):
        try:
            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            fields = reader.fieldnames or []
            all_fields.update(fields)
            participants = sorted({str(r.get("user", "")).strip() for r in rows if str(r.get("user", "")).strip()})
            log_rows_with_prediction = sum(1 for r in rows if str(r.get("pred_label", "")).strip())
            log_rows_with_timing = sum(1 for r in rows if any(str(r.get(field, "")).strip() for field in BOARD_TIMING_FIELDS))
            row_count += len(rows)
            rows_with_prediction += log_rows_with_prediction
            rows_with_timing += log_rows_with_timing
            logs.append(
                {
                    "path": str(path.resolve()),
                    "rows": len(rows),
                    "participants": participants,
                    "has_board_prediction": bool(log_rows_with_prediction),
                    "has_timing_fields": bool(log_rows_with_timing),
                    "fields": fields,
                }
            )
            for row in rows:
                wav_path = str(row.get("wav_path", "")).strip()
                wav_filename = Path(wav_path).name if wav_path else f"{row.get('repeat_idx', '')}.wav"
                key = board_log_key(
                    str(row.get("user", path.parent.name)),
                    str(row.get("intent", "")),
                    str(row.get("keyword", "")),
                    wav_filename,
                )
                enriched = dict(row)
                enriched["source_results_csv"] = str(path.resolve())
                if key in joined_by_key:
                    duplicate_keys.append(
                        {
                            "key": "|".join(key),
                            "first_results_csv": joined_by_key[key].get("source_results_csv", ""),
                            "duplicate_results_csv": str(path.resolve()),
                        }
                    )
                else:
                    joined_by_key[key] = enriched
        except Exception as exc:  # noqa: BLE001
            logs.append({"path": str(path.resolve()), "error": str(exc)})
    audit = {
        "input_root": str(input_root.resolve()),
        "results_csv_count": len(logs),
        "row_count": row_count,
        "rows_with_prediction": rows_with_prediction,
        "rows_with_timing": rows_with_timing,
        "fields": sorted(all_fields),
        "logs": logs,
        "duplicate_join_keys": duplicate_keys,
    }
    return joined_by_key, audit


def board_log_for_trial(trial: dict[str, Any], board_logs: dict[tuple[str, str, str, str], dict[str, Any]]) -> dict[str, Any] | None:
    keyword = str(trial.get("keyword", ""))
    if not keyword or keyword == "unavailable_in_sd_path":
        return None
    key = board_log_key(
        str(trial.get("participant_id", "")),
        str(trial.get("intent_ground_truth", "")),
        keyword,
        Path(str(trial.get("audio_path", ""))).name,
    )
    return board_logs.get(key)


def finalize_board_log_audit(
    input_audit: dict[str, Any],
    external_audit: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    with_board = [r for r in rows if str(r.get("board_prediction", "")).strip()]
    agreement = [r for r in with_board if r.get("recomputed_matches_board") is True]
    mismatches = [r for r in with_board if r.get("recomputed_matches_board") is False]
    agreement_rate = float(len(agreement) / len(with_board)) if with_board else None
    mismatch_examples = [
        {
            "participant_id": r["participant_id"],
            "intent_ground_truth": r["intent_ground_truth"],
            "keyword": r["keyword"],
            "repeat_idx": r["repeat_idx"],
            "predicted_intent": r["predicted_intent"],
            "board_prediction": r["board_prediction"],
            "audio_relpath": r["audio_relpath"],
        }
        for r in mismatches[:10]
    ]
    return {
        "input_results_csv_count": input_audit.get("results_csv_count", 0),
        "input_board_log_rows": input_audit.get("row_count", 0),
        "input_rows_with_prediction": input_audit.get("rows_with_prediction", 0),
        "input_rows_with_timing": input_audit.get("rows_with_timing", 0),
        "input_board_log_fields": input_audit.get("fields", []),
        "input_board_logs": input_audit.get("logs", []),
        "duplicate_join_keys": input_audit.get("duplicate_join_keys", []),
        "used_for_trial_join": True,
        "trials_with_board_prediction": len(with_board),
        "recomputed_agreement_count": len(agreement),
        "recomputed_agreement_rate": agreement_rate,
        "mismatch_count": len(mismatches),
        "mismatch_examples": mismatch_examples,
        "external_event_log_count": external_audit.get("event_log_count", 0),
        "external_logs": external_audit.get("logs", []),
        "join_note": (
            "Input-root results.csv files are joined by participant, intent, keyword, and WAV filename. "
            "Flat legacy participant/keyword directories have no input results.csv rows and therefore keep empty board fields."
        ),
    }


def load_external_board_log_audit(root: Path) -> dict[str, Any]:
    logs = []
    if root.exists():
        for path in sorted(root.rglob("*events.csv")):
            try:
                with path.open("r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                board_rows = [r for r in rows if r.get("pred_label") or r.get("raw_json")]
                participants = sorted({str(r.get("user", "")).strip() for r in rows if str(r.get("user", "")).strip()})
                fields = reader.fieldnames or []
                logs.append(
                    {
                        "path": str(path.resolve()),
                        "rows": len(rows),
                        "participants": participants,
                        "has_board_prediction": bool(board_rows),
                        "has_timing_fields": any(f in fields for f in ["capture_ms", "frontend_ms", "infer_ms", "total_ms", "rtt_ms"]),
                        "fields": fields,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logs.append({"path": str(path.resolve()), "error": str(exc)})
    usable_direct_matches = 0
    return {
        "root": str(root.resolve()),
        "event_log_count": len(logs),
        "logs": logs,
        "used_for_trial_join": False,
        "usable_direct_matches": usable_direct_matches,
        "join_note": (
            "External host logs exist outside the SD input root, but the provided SD tree is flattened "
            "as participant/intent/index.wav and does not preserve board keyword/capture-id paths. "
            "No board prediction is joined without an explicit path mapping."
        ),
    }


class TFLiteRunner:
    def __init__(self, model_path: Path, label_encoder_path: Path):
        self.model_path = model_path.resolve()
        self.label_encoder_path = label_encoder_path.resolve()
        label_encoder = joblib.load(self.label_encoder_path)
        self.class_names = [str(v) for v in label_encoder.classes_]
        self.interpreter = tf.lite.Interpreter(model_path=str(self.model_path))
        self.interpreter.allocate_tensors()
        self.input_detail = self.interpreter.get_input_details()[0]
        self.output_detail = self.interpreter.get_output_details()[0]

    @staticmethod
    def quantize(array: np.ndarray, tensor_detail: dict[str, Any]) -> np.ndarray:
        dtype = np.dtype(tensor_detail["dtype"])
        if dtype not in (np.int8, np.uint8):
            return array.astype(dtype, copy=False)
        scale, zero_point = tensor_detail.get("quantization", (0.0, 0))
        if not scale:
            raise RuntimeError(f"Missing input quantization for {tensor_detail.get('name')}")
        q = np.round(array / float(scale) + float(zero_point))
        info = np.iinfo(dtype)
        return np.clip(q, info.min, info.max).astype(dtype, copy=False)

    @staticmethod
    def dequantize(array: np.ndarray, tensor_detail: dict[str, Any]) -> np.ndarray:
        dtype = np.dtype(tensor_detail["dtype"])
        if dtype not in (np.int8, np.uint8):
            return array.astype(np.float32, copy=False)
        scale, zero_point = tensor_detail.get("quantization", (0.0, 0))
        if not scale:
            raise RuntimeError(f"Missing output quantization for {tensor_detail.get('name')}")
        return (array.astype(np.float32) - float(zero_point)) * float(scale)

    def describe(self) -> dict[str, Any]:
        return {
            "model_path": str(self.model_path),
            "model_sha256": sha256(self.model_path),
            "label_encoder_path": str(self.label_encoder_path),
            "class_names": self.class_names,
            "input_name": str(self.input_detail.get("name")),
            "input_shape": [int(v) for v in self.input_detail["shape"].tolist()],
            "input_dtype": str(np.dtype(self.input_detail["dtype"])),
            "input_quantization": [float(self.input_detail["quantization"][0]), int(self.input_detail["quantization"][1])],
            "output_name": str(self.output_detail.get("name")),
            "output_shape": [int(v) for v in self.output_detail["shape"].tolist()],
            "output_dtype": str(np.dtype(self.output_detail["dtype"])),
            "output_quantization": [float(self.output_detail["quantization"][0]), int(self.output_detail["quantization"][1])],
        }

    def predict_wav(self, path: Path) -> dict[str, Any]:
        total_start = time.perf_counter()
        read_start = time.perf_counter()
        with wave.open(str(path), "rb") as w:
            pcm_bytes = w.readframes(w.getnframes())
        read_ms = (time.perf_counter() - read_start) * 1000.0

        frontend_start = time.perf_counter()
        pcm = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32)
        waveform = ensure_target_len(np.clip(pcm / 32768.0, -1.0, 1.0))
        mel = extract_logmel_input(waveform)
        model_input = np.expand_dims(mel, axis=0).astype(np.float32, copy=False)
        model_input = self.quantize(model_input, self.input_detail)
        frontend_ms = (time.perf_counter() - frontend_start) * 1000.0

        invoke_start = time.perf_counter()
        self.interpreter.set_tensor(self.input_detail["index"], model_input)
        self.interpreter.invoke()
        raw_output = self.interpreter.get_tensor(self.output_detail["index"])
        invoke_ms = (time.perf_counter() - invoke_start) * 1000.0

        probs = self.dequantize(raw_output, self.output_detail)[0]
        pred_idx = int(np.argmax(probs))
        return {
            "predicted_intent": self.class_names[pred_idx],
            "confidence": float(probs[pred_idx]),
            "probabilities": {self.class_names[i]: float(probs[i]) for i in range(len(self.class_names))},
            "raw_output_int8": [int(v) for v in raw_output.reshape(-1).tolist()],
            "audio_read_ms": read_ms,
            "frontend_ms": frontend_ms,
            "tflite_invoke_ms": invoke_ms,
            "host_total_ms": (time.perf_counter() - total_start) * 1000.0,
        }


def choose_smoke_trials(trials: list[dict[str, Any]], per_intent: int) -> list[dict[str, Any]]:
    chosen: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for row in trials:
        intent = row["intent_ground_truth"]
        if counts[intent] < per_intent:
            chosen.append(row)
            counts[intent] += 1
        if all(counts[c] >= per_intent for c in CLASS_ORDER):
            break
    return chosen


def infer_trials(
    trials: list[dict[str, Any]],
    runner: TFLiteRunner,
    board_logs: dict[tuple[str, str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for idx, trial in enumerate(trials, start=1):
        pred = runner.predict_wav(Path(trial["audio_path"]))
        board = board_log_for_trial(trial, board_logs) or {}
        board_prediction = str(board.get("pred_label", "")).strip()
        recomputed_matches_board: bool | str = ""
        if board_prediction:
            recomputed_matches_board = pred["predicted_intent"] == board_prediction
        row = {
            "trial_id": idx,
            "participant_id": trial["participant_id"],
            "intent_ground_truth": trial["intent_ground_truth"],
            "keyword": trial["keyword"],
            "repeat_idx": trial["repeat_idx"],
            "label_source": trial.get("label_source", ""),
            "audio_path": trial["audio_path"],
            "audio_relpath": trial["audio_relpath"],
            "predicted_intent": pred["predicted_intent"],
            "confidence": pred["confidence"],
            "correct": pred["predicted_intent"] == trial["intent_ground_truth"],
            "board_prediction": board_prediction,
            "board_confidence": board.get("confidence", ""),
            "recomputed_matches_board": recomputed_matches_board,
            "board_err_code": board.get("err_code", ""),
            "board_capture_ms": board.get("capture_ms", ""),
            "board_frontend_ms": board.get("frontend_ms", ""),
            "board_infer_ms": board.get("infer_ms", ""),
            "board_total_ms": board.get("total_ms", ""),
            "board_raw_output_int8": json.dumps([int(board[f"raw{i}"]) for i in range(3) if str(board.get(f"raw{i}", "")).strip()]) if board else "",
            "board_model_sha256": board.get("model_sha256", ""),
            "board_build_tag": board.get("build_tag", ""),
            "board_results_csv": board.get("source_results_csv", ""),
            "audio_read_ms": pred["audio_read_ms"],
            "frontend_ms": pred["frontend_ms"],
            "tflite_invoke_ms": pred["tflite_invoke_ms"],
            "host_total_ms": pred["host_total_ms"],
            "raw_output_int8": json.dumps(pred["raw_output_int8"]),
        }
        for label, value in pred["probabilities"].items():
            row[f"prob_{label}"] = value
        predictions.append(row)
    return predictions


def prfs(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict[str, dict[str, float]]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
    return {
        label: {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
        }
        for i, label in enumerate(labels)
    }


def macro_f1(y_true: list[str], y_pred: list[str], labels: list[str]) -> float:
    _, _, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return float(np.mean(f1)) if len(f1) else 0.0


def unknown_false_event_rate(rows: list[dict[str, Any]]) -> float | None:
    unknown_rows = [r for r in rows if r["intent_ground_truth"] == "unknown"]
    if not unknown_rows:
        return None
    false_events = [r for r in unknown_rows if r["predicted_intent"] != "unknown"]
    return float(len(false_events) / len(unknown_rows))


def build_metrics(rows: list[dict[str, Any]], labels: list[str]) -> dict[str, Any]:
    y_true = [str(r["intent_ground_truth"]) for r in rows]
    y_pred = [str(r["predicted_intent"]) for r in rows]
    per_class = prfs(y_true, y_pred, labels)
    return {
        "total_trials": len(rows),
        "overall_accuracy": float(accuracy_score(y_true, y_pred)) if rows else 0.0,
        "macro_f1": macro_f1(y_true, y_pred, labels),
        "emergency_precision": per_class["emergency"]["precision"],
        "emergency_recall": per_class["emergency"]["recall"],
        "emergency_f1": per_class["emergency"]["f1"],
        "movement_recall": per_class["movement"]["recall"],
        "movement_f1": per_class["movement"]["f1"],
        "unknown_false_event_rate": unknown_false_event_rate(rows),
        "per_class": per_class,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def format_float(value: Any, digits: int = 4) -> str:
    if value is None or value == "":
        return "NA"
    return f"{float(value):.{digits}f}"


def participant_summary(rows: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["participant_id"]].append(row)
    out = []
    for participant in sorted(grouped):
        subset = grouped[participant]
        metrics = build_metrics(subset, labels)
        out.append(
            {
                "participant": participant,
                "trials": metrics["total_trials"],
                "overall_accuracy": metrics["overall_accuracy"],
                "emergency_recall": metrics["emergency_recall"],
                "movement_recall": metrics["movement_recall"],
                "unknown_false_event_rate": metrics["unknown_false_event_rate"],
                "macro_f1": metrics["macro_f1"],
            }
        )
    return out


def intent_summary(rows: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
    metrics = build_metrics(rows, labels)["per_class"]
    return [
        {
            "intent": label,
            "support": metrics[label]["support"],
            "precision": metrics[label]["precision"],
            "recall": metrics[label]["recall"],
            "f1": metrics[label]["f1"],
        }
        for label in labels
    ]


def keyword_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["intent_ground_truth"], row["keyword"])].append(row)
    out = []
    for (intent, keyword), subset in sorted(grouped.items()):
        wrong = [r["predicted_intent"] for r in subset if not r["correct"]]
        common_wrong = ""
        if wrong:
            common_wrong = Counter(wrong).most_common(1)[0][0]
        out.append(
            {
                "intent": intent,
                "keyword": keyword,
                "support": len(subset),
                "accuracy": sum(1 for r in subset if r["correct"]) / len(subset),
                "most_common_wrong_prediction": common_wrong,
            }
        )
    return out


def confusion_rows(rows: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
    y_true = [str(r["intent_ground_truth"]) for r in rows]
    y_pred = [str(r["predicted_intent"]) for r in rows]
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    out = []
    for i, true_label in enumerate(labels):
        row = {"true_intent": true_label}
        for j, pred_label in enumerate(labels):
            row[f"pred_{pred_label}"] = int(matrix[i, j])
        out.append(row)
    return out


def board_consistency_rows(board_log_audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "trials_with_board_prediction": board_log_audit.get("trials_with_board_prediction", 0),
            "recomputed_agreement_count": board_log_audit.get("recomputed_agreement_count", 0),
            "recomputed_agreement_rate": board_log_audit.get("recomputed_agreement_rate", ""),
            "mismatch_count": board_log_audit.get("mismatch_count", 0),
            "input_results_csv_count": board_log_audit.get("input_results_csv_count", 0),
            "input_board_log_rows": board_log_audit.get("input_board_log_rows", 0),
            "input_rows_with_timing": board_log_audit.get("input_rows_with_timing", 0),
        }
    ]


def board_mismatch_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "trial_id",
        "participant_id",
        "intent_ground_truth",
        "keyword",
        "repeat_idx",
        "audio_relpath",
        "predicted_intent",
        "confidence",
        "board_prediction",
        "board_confidence",
        "board_results_csv",
    ]
    return [
        {field: row.get(field, "") for field in fields}
        for row in rows
        if row.get("recomputed_matches_board") is False
    ]


def write_missing_expected(path: Path, data_audit: dict[str, Any]) -> None:
    rows = data_audit.get("missing_against_full_50_per_intent", [])
    write_csv(
        path,
        rows,
        [
            "participant_id",
            "intent",
            "expected_files_if_full_50",
            "observed_files",
            "missing_count",
            "extra_count",
            "delta_observed_minus_expected",
        ],
    )


def build_candidate_audit(args: argparse.Namespace, runner_desc: dict[str, Any]) -> dict[str, Any]:
    current_rt1s = {
        "candidate_name": args.candidate_name,
        "selected": True,
        "selection_reason": (
            "Current ESP32 user-study CDC+SD firmware config and host capture script name "
            "xiao_rt1s_c32_b256_samearch_ts as runtime candidate."
        ),
        "tflite_path": str(args.tflite.resolve()),
        "model_test_info_path": str(args.model_test_info.resolve()),
        "tflm_precheck_path": str(args.tflm_precheck.resolve()),
        "run_config_path": str(args.run_config.resolve()),
        "firmware_config_path": str(args.firmware_config.resolve()),
        "runner": runner_desc,
        "model_test_info": read_json(args.model_test_info),
        "tflm_precheck_summary": {
            k: v
            for k, v in read_json(args.tflm_precheck).items()
            if k
            in {
                "model",
                "size_bytes",
                "input_details",
                "output_details",
                "op_counts",
                "compatibility_gate",
            }
        },
        "run_config": read_json(args.run_config),
    }
    b_small = {
        "candidate_name": "B_small_teacher_student",
        "selected": False,
        "selection_reason": "Frozen deployment candidate artifact exists, but it is not the runtime candidate named by current CDC+SD firmware.",
        "tflite_path": str((REPO_ROOT / "realworld" / "esp32" / "phase2_artifacts" / "B_small_teacher_student_full_integer.tflite").resolve()),
        "model_info_path": str((REPO_ROOT / "realworld" / "esp32" / "models" / "B_small_teacher_student" / "MODEL_INFO.json").resolve()),
        "run_config_path": str((REPO_ROOT / "weeklyresult" / "weekly_drone_2026w17" / "B_small_teacher_student" / "run_config.json").resolve()),
    }
    return {
        "selected_candidate": current_rt1s,
        "other_candidates_considered": [b_small],
        "frontend": {
            "sample_rate_hz": 16000,
            "window_length_samples": 16000,
            "duration_sec": 1.0,
            "n_fft": 1024,
            "hop_length": 512,
            "center": False,
            "n_mels": 256,
            "fmin_hz": 50,
            "fmax_hz": None,
            "top_db": 80.0,
            "max_frames": 32,
            "frontend_config_path": str(args.frontend_config.resolve()),
            "frontend_shared_path": str(args.frontend_shared.resolve()),
            "frontend_constants_path": str(args.frontend_constants.resolve()),
        },
        "label_mapping": {
            "label_encoder_path": str(args.label_encoder.resolve()),
            "class_names": runner_desc["class_names"],
        },
        "quantization_inference_path": {
            "runtime": "TensorFlow Lite full-integer int8 desktop interpreter using deployment TFLite model",
            "input_quantization": runner_desc["input_quantization"],
            "output_quantization": runner_desc["output_quantization"],
            "note": "This recomputes offline desktop TFLite predictions with the ESP32 candidate model and shared frontend; it is not a live board run.",
        },
    }


def build_latex(metrics: dict[str, Any], participants: list[dict[str, Any]], intents: list[dict[str, Any]], keywords: list[dict[str, Any]]) -> str:
    lines = [
        "# Paper-Ready LaTeX Rows",
        "",
        "Claim boundary: controlled user-study audio reinference; not live-flight validation.",
        "",
        "## Overall User-Study Row",
        "",
        "```latex",
        (
            "User study audio reinference & "
            f"{metrics['total_trials']} & "
            f"{metrics['overall_accuracy'] * 100:.1f}\\% & "
            f"{metrics['macro_f1']:.3f} & "
            f"{metrics['emergency_precision']:.3f} & "
            f"{metrics['emergency_recall']:.3f} & "
            f"{metrics['movement_recall']:.3f} & "
            f"{(metrics['unknown_false_event_rate'] or 0.0) * 100:.1f}\\% \\\\"
        ),
        "```",
        "",
        "## Participant Rows",
        "",
        "```latex",
    ]
    for row in participants:
        lines.append(
            f"{row['participant']} & {row['trials']} & "
            f"{row['overall_accuracy'] * 100:.1f}\\% & "
            f"{row['emergency_recall']:.3f} & "
            f"{row['movement_recall']:.3f} & "
            f"{format_float(row['unknown_false_event_rate'], 3)} & "
            f"{row['macro_f1']:.3f} \\\\"
        )
    lines.extend(["```", "", "## Intent Rows", "", "```latex"])
    for row in intents:
        lines.append(
            f"{row['intent']} & {row['support']} & "
            f"{row['precision']:.3f} & {row['recall']:.3f} & {row['f1']:.3f} \\\\"
        )
    lines.extend(["```", "", "## Keyword Rows", ""])
    if len(keywords) == 3 and all(k["keyword"] == "unavailable_in_sd_path" for k in keywords):
        lines.append("Keyword-level rows are unavailable because the supplied SD tree does not encode keyword in the path.")
    else:
        lines.append("```latex")
        for row in keywords:
            lines.append(
                f"{row['intent']} & {row['keyword']} & {row['support']} & "
                f"{row['accuracy'] * 100:.1f}\\% & {row['most_common_wrong_prediction'] or '--'} \\\\"
            )
        lines.append("```")
    lines.append("")
    return "\n".join(lines)


def build_report(
    args: argparse.Namespace,
    metrics: dict[str, Any],
    participant_rows: list[dict[str, Any]],
    intent_rows: list[dict[str, Any]],
    keyword_rows: list[dict[str, Any]],
    data_audit: dict[str, Any],
    candidate_audit: dict[str, Any],
    board_log_audit: dict[str, Any],
    skipped: list[dict[str, Any]],
    exact_command: str,
) -> str:
    dirty = run_git(["status", "--short", "--branch"])
    audio_formats = ", ".join(
        f"{fmt}: {count}" for fmt, count in sorted(data_audit["audio_format_counts"].items())
    )
    observed_structures = ", ".join(data_audit.get("observed_structures", [])) or "none"
    label_source_counts = ", ".join(
        f"{source}: {count}" for source, count in sorted(data_audit.get("label_source_counts", {}).items())
    )
    board_agreement = format_float(board_log_audit.get("recomputed_agreement_rate"), 4)
    mapping_lines = []
    if data_audit.get("legacy_keyword_mapping_used"):
        by_intent: dict[str, list[str]] = defaultdict(list)
        for keyword, intent in sorted(data_audit.get("legacy_keyword_mapping", {}).items()):
            by_intent[str(intent)].append(str(keyword))
        mapping_lines = [
            f"- legacy flat keyword mapping used: true",
            f"- legacy mapping emergency keywords: `{', '.join(by_intent.get('emergency', []))}`",
            f"- legacy mapping movement keywords: `{', '.join(by_intent.get('movement', []))}`",
            f"- legacy mapping unknown keywords: `{', '.join(by_intent.get('unknown', []))}`",
        ]
    else:
        mapping_lines = ["- legacy flat keyword mapping used: false"]
    board_section_lines = [
        "",
        "## Board Consistency",
        "",
        "| trials with board prediction | agreement rate | mismatch count |",
        "|---:|---:|---:|",
        (
            f"| {board_log_audit['trials_with_board_prediction']} | "
            f"{board_agreement} | {board_log_audit['mismatch_count']} |"
        ),
    ]
    if board_log_audit.get("mismatch_examples"):
        board_section_lines.extend(["", "Mismatch examples are written to `board_mismatch_examples.csv`; first examples:"])
        for item in board_log_audit["mismatch_examples"][:5]:
            board_section_lines.append(
                "- "
                f"{item['audio_relpath']}: recomputed={item['predicted_intent']}, "
                f"board={item['board_prediction']}, gt={item['intent_ground_truth']}"
            )
    lines = [
        f"# {args.dataset_name} ESP32 Candidate Re-Inference",
        "",
        "Claim boundary: this is controlled user-study SD audio reinference with the local ESP32 candidate recognizer. It is not live-flight validation and not semantic safety validation.",
        "",
        "## Run Context",
        "",
        f"- branch: `{run_git(['branch', '--show-current'])}`",
        f"- HEAD: `{run_git(['rev-parse', 'HEAD'])}`",
        "- dirty status:",
        "",
        "```text",
        dirty,
        "```",
        "",
        f"- exact command: `{exact_command}`",
        f"- input data path: `{args.input_root.resolve()}`",
        f"- output path: `{args.output_dir.resolve()}`",
        "",
        "## Model And Frontend",
        "",
        f"- selected model: `{args.candidate_name}`",
        f"- selection rationale: {candidate_audit['selected_candidate']['selection_reason']}",
        "- other candidate considered: `B_small_teacher_student` exists as a frozen deployment artifact, but it is not the runtime candidate named by the current CDC+SD firmware.",
        f"- model path: `{args.tflite.resolve()}`",
        f"- model sha256: `{sha256(args.tflite)}`",
        f"- model metadata: `{args.model_test_info.resolve()}`",
        f"- run config: `{args.run_config.resolve()}`",
        f"- frontend config: `{args.frontend_config.resolve()}`",
        f"- frontend shared implementation: `{args.frontend_shared.resolve()}`",
        f"- ESP32 frontend constants: `{args.frontend_constants.resolve()}`",
        f"- label mapping: `{args.label_encoder.resolve()}` -> `{', '.join(candidate_audit['label_mapping']['class_names'])}`",
        "- frontend parameters: sample_rate=16000 Hz, window=16000 samples, n_fft=1024, hop=512, center=False, n_mels=256, fmin=50 Hz, fmax=None, top_db=80, max_frames=32",
        f"- quantization: input `{candidate_audit['quantization_inference_path']['input_quantization']}`, output `{candidate_audit['quantization_inference_path']['output_quantization']}`",
        "",
        "## Input Data Audit",
        "",
        f"- observed structures: `{observed_structures}`",
        "- participant/user id: first-level directory name",
        "- intent: second-level intent directory when present; for early flat keyword directories, intent is assigned only by the documented legacy keyword mapping below",
        "- keyword: third-level directory for intent-structured trials; second-level directory for early flat trials",
        "- repeat/index: WAV filename stem, recorded as `repeat_idx`",
        f"- label source counts: {label_source_counts}",
        *mapping_lines,
        f"- audio file format counts: {audio_formats}",
        f"- participants: {data_audit['participant_count']} (`{', '.join(data_audit['participants'])}`)",
        f"- valid trials: {data_audit['valid_trial_count']}",
        f"- skipped/invalid files: {data_audit['skipped_count']}",
        f"- expected full intent grid if every participant had 3 intents x 50 files: {data_audit['expected_full_intent_grid_trials']}",
        f"- missing files against modern 3x50-per-participant reference grid: {data_audit['missing_file_count_against_modern_full_50']}",
        f"- extra files against modern 3x50-per-participant reference grid: {data_audit['extra_file_count_against_modern_full_50']}",
        f"- keyword encoded in SD path: {data_audit['keyword_encoded_in_sd_path']}",
        f"- board logs inside input root: {data_audit['board_logs_inside_input_root']}",
        f"- input results.csv count: {board_log_audit['input_results_csv_count']}",
        f"- input board log rows: {board_log_audit['input_board_log_rows']}",
        f"- input board log rows with timing/log fields: {board_log_audit['input_rows_with_timing']}",
        f"- external board event logs found: {board_log_audit['external_event_log_count']}",
        f"- board log join: {board_log_audit['join_note']}",
        f"- trials with board prediction: {board_log_audit['trials_with_board_prediction']}",
        f"- recomputed-board agreement rate: {board_agreement}",
        f"- recomputed-board mismatch count: {board_log_audit['mismatch_count']}",
        "",
        "## Final Metrics",
        "",
        f"- total trials: {metrics['total_trials']}",
        f"- overall accuracy: {metrics['overall_accuracy']:.4f}",
        f"- macro F1: {metrics['macro_f1']:.4f}",
        f"- emergency precision / recall / F1: {metrics['emergency_precision']:.4f} / {metrics['emergency_recall']:.4f} / {metrics['emergency_f1']:.4f}",
        f"- movement recall / F1: {metrics['movement_recall']:.4f} / {metrics['movement_f1']:.4f}",
        f"- unknown false event rate: {format_float(metrics['unknown_false_event_rate'], 4)}",
        *board_section_lines,
        "",
        "## Participant Summary",
        "",
        "| participant | trials | accuracy | emergency recall | movement recall | unknown false event rate | macro F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in participant_rows:
        lines.append(
            f"| {row['participant']} | {row['trials']} | {row['overall_accuracy']:.4f} | "
            f"{row['emergency_recall']:.4f} | {row['movement_recall']:.4f} | "
            f"{format_float(row['unknown_false_event_rate'], 4)} | {row['macro_f1']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Intent Summary",
            "",
            "| intent | support | precision | recall | F1 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in intent_rows:
        lines.append(
            f"| {row['intent']} | {row['support']} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Keyword Summary",
            "",
        ]
    )
    if len(keyword_rows) == 3 and all(k["keyword"] == "unavailable_in_sd_path" for k in keyword_rows):
        lines.append("Keyword-level metrics are not available from the supplied SD tree because keyword is not encoded in the path and keyword-plan inference was explicitly not used.")
    else:
        lines.extend(["| intent | keyword | support | accuracy | most common wrong prediction |", "|---|---|---:|---:|---|"])
        for row in keyword_rows:
            lines.append(
                f"| {row['intent']} | {row['keyword']} | {row['support']} | {row['accuracy']:.4f} | {row['most_common_wrong_prediction']} |"
            )
    lines.extend(["", "## Skipped Or Invalid Files", ""])
    if skipped:
        lines.append("| audio_path | reason |")
        lines.append("|---|---|")
        for row in skipped[:50]:
            lines.append(f"| `{row.get('audio_path', '')}` | {row.get('reason', '')} |")
        if len(skipped) > 50:
            lines.append(f"| ... | {len(skipped) - 50} more rows in skipped_invalid.csv |")
    else:
        lines.append("No invalid WAV files were skipped.")
    lines.extend(
        [
            "",
            "## Artifact Paths",
            "",
            "- `trial_predictions.csv`",
            "- `participant_summary.csv`",
            "- `intent_summary.csv`",
            "- `keyword_summary.csv`",
            "- `confusion_matrix.csv`",
            "- `run_manifest.json`",
            "- `latex_tables.md`",
            "- `missing_expected_trials.csv`",
            "- `skipped_invalid.csv`",
            "- `legacy_keyword_mapping.json`",
            "- `board_consistency.csv`",
            "- `board_mismatch_examples.csv`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    trials, skipped, data_audit = scan_trials(args.input_root)
    if args.mode == "smoke":
        run_output_dir = args.output_dir / "smoke"
        run_trials = choose_smoke_trials(trials, args.smoke_per_intent)
    else:
        run_output_dir = args.output_dir
        run_trials = trials
    run_output_dir.mkdir(parents=True, exist_ok=True)

    if not run_trials:
        raise RuntimeError("No valid WAV trials found for the requested mode.")

    runner = TFLiteRunner(args.tflite, args.label_encoder)
    runner_desc = runner.describe()
    if runner_desc["class_names"] != CLASS_ORDER:
        raise RuntimeError(f"Unexpected label mapping: {runner_desc['class_names']} != {CLASS_ORDER}")

    input_board_logs, input_board_log_audit = load_input_board_logs(args.input_root)
    rows = infer_trials(run_trials, runner, input_board_logs)
    metrics = build_metrics(rows, CLASS_ORDER)
    participant_rows = participant_summary(rows, CLASS_ORDER)
    intent_rows = intent_summary(rows, CLASS_ORDER)
    keyword_rows = keyword_summary(rows)
    confusion = confusion_rows(rows, CLASS_ORDER)
    candidate_audit = build_candidate_audit(args, runner_desc)
    external_board_log_audit = load_external_board_log_audit(args.external_board_log_root)
    board_log_audit = finalize_board_log_audit(input_board_log_audit, external_board_log_audit, rows)
    env_keys = ["MPLCONFIGDIR", "NUMBA_CACHE_DIR", "TF_CPP_MIN_LOG_LEVEL"]
    env_prefix = [f"{key}={os.environ[key]}" for key in env_keys if os.environ.get(key)]
    exact_command = " ".join(["env", *env_prefix, sys.executable, *sys.argv])

    prediction_fields = [
        "trial_id",
        "participant_id",
        "intent_ground_truth",
        "keyword",
        "repeat_idx",
        "label_source",
        "audio_path",
        "audio_relpath",
        "predicted_intent",
        "confidence",
        "prob_emergency",
        "prob_movement",
        "prob_unknown",
        "raw_output_int8",
        "correct",
        "board_prediction",
        "board_confidence",
        "recomputed_matches_board",
        "board_err_code",
        "board_capture_ms",
        "board_frontend_ms",
        "board_infer_ms",
        "board_total_ms",
        "board_raw_output_int8",
        "board_model_sha256",
        "board_build_tag",
        "board_results_csv",
        "audio_read_ms",
        "frontend_ms",
        "tflite_invoke_ms",
        "host_total_ms",
    ]
    write_csv(run_output_dir / "trial_predictions.csv", rows, prediction_fields)
    write_csv(run_output_dir / "participant_summary.csv", participant_rows)
    write_csv(run_output_dir / "intent_summary.csv", intent_rows)
    write_csv(run_output_dir / "keyword_summary.csv", keyword_rows)
    write_csv(run_output_dir / "confusion_matrix.csv", confusion)
    write_csv(run_output_dir / "skipped_invalid.csv", skipped)
    write_missing_expected(run_output_dir / "missing_expected_trials.csv", data_audit)
    (run_output_dir / "legacy_keyword_mapping.json").write_text(
        json.dumps(data_audit.get("legacy_keyword_mapping", {}), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    write_csv(run_output_dir / "board_consistency.csv", board_consistency_rows(board_log_audit))
    write_csv(run_output_dir / "board_mismatch_examples.csv", board_mismatch_rows(rows))

    manifest = {
        "dataset_name": args.dataset_name,
        "mode": args.mode,
        "created_at_epoch": time.time(),
        "exact_command": exact_command,
        "repo": {
            "root": str(REPO_ROOT),
            "branch": run_git(["branch", "--show-current"]),
            "head": run_git(["rev-parse", "HEAD"]),
            "status_short_branch": run_git(["status", "--short", "--branch"]),
        },
        "input_data": data_audit,
        "selected_trials": len(run_trials),
        "candidate_audit": candidate_audit,
        "board_log_audit": board_log_audit,
        "metrics": metrics,
        "outputs": {
            "trial_predictions_csv": str((run_output_dir / "trial_predictions.csv").resolve()),
            "participant_summary_csv": str((run_output_dir / "participant_summary.csv").resolve()),
            "intent_summary_csv": str((run_output_dir / "intent_summary.csv").resolve()),
            "keyword_summary_csv": str((run_output_dir / "keyword_summary.csv").resolve()),
            "confusion_matrix_csv": str((run_output_dir / "confusion_matrix.csv").resolve()),
            "run_manifest_json": str((run_output_dir / "run_manifest.json").resolve()),
            "report_md": str((run_output_dir / "report.md").resolve()),
            "latex_tables_md": str((run_output_dir / "latex_tables.md").resolve()),
            "missing_expected_trials_csv": str((run_output_dir / "missing_expected_trials.csv").resolve()),
            "skipped_invalid_csv": str((run_output_dir / "skipped_invalid.csv").resolve()),
            "legacy_keyword_mapping_json": str((run_output_dir / "legacy_keyword_mapping.json").resolve()),
            "board_consistency_csv": str((run_output_dir / "board_consistency.csv").resolve()),
            "board_mismatch_examples_csv": str((run_output_dir / "board_mismatch_examples.csv").resolve()),
        },
    }
    (run_output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (run_output_dir / "latex_tables.md").write_text(
        build_latex(metrics, participant_rows, intent_rows, keyword_rows),
        encoding="utf-8",
    )
    (run_output_dir / "report.md").write_text(
        build_report(
            args,
            metrics,
            participant_rows,
            intent_rows,
            keyword_rows,
            data_audit,
            candidate_audit,
            board_log_audit,
            skipped,
            exact_command,
        ),
        encoding="utf-8",
    )

    print(json.dumps({"mode": args.mode, "output_dir": str(run_output_dir.resolve()), "metrics": metrics}, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    main()
