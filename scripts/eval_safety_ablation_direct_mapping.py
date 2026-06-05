#!/usr/bin/env python3
"""Evaluate direct-action mapping and no-unknown containment ablations.

This script does not run any recognizer. It consumes existing prediction or
confusion artifacts and simulates how many windows would become actionable if
predicted intents were mapped directly to UAV actions without the safety-state
boundary.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
LABELS = ("emergency", "movement", "unknown")
ACTIONABLE = {"emergency", "movement"}


@dataclass
class Source:
    source_id: str
    source_role: str
    population: str
    evidence_type: str
    path: Path
    true_labels: list[str] | None
    pred_labels: list[str] | None
    confusion_matrix: list[list[int]]
    probabilities: dict[str, list[float]] | None
    sequence_available: bool
    caveat: str


def abs_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover
        return f"UNAVAILABLE: {exc}"


def shell_command() -> str:
    return "python3 " + " ".join(shlex.quote(part) for part in sys.argv)


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)
        f.write("\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def confusion_from_labels(true_labels: list[str], pred_labels: list[str]) -> list[list[int]]:
    idx = {name: i for i, name in enumerate(LABELS)}
    cm = np.zeros((len(LABELS), len(LABELS)), dtype=int)
    for t, p in zip(true_labels, pred_labels):
        if t not in idx or p not in idx:
            raise RuntimeError(f"Unknown label pair: true={t!r}, pred={p!r}")
        cm[idx[t], idx[p]] += 1
    return cm.astype(int).tolist()


def load_asr_source(path: Path) -> Source:
    rows = read_csv(path)
    rows = [r for r in rows if str(r.get("asr_failed", "0")) != "1"]
    true_labels = [r["true_label"].strip().lower() for r in rows]
    pred_labels = [r["predicted_intent"].strip().lower() for r in rows]
    return Source(
        source_id="asr_whisper_tiny_parser_snr_m10db",
        source_role="transcript_first_asr_parser",
        population="Speech Commands X_test fixed noisy condition, snr_m10db=-10 dB",
        evidence_type="per_sample_labels",
        path=path,
        true_labels=true_labels,
        pred_labels=pred_labels,
        confusion_matrix=confusion_from_labels(true_labels, pred_labels),
        probabilities=None,
        sequence_available=True,
        caveat="Per-sample row order is the held-out split order, not a real continuous flight sequence; consecutive-action metrics are adjacency diagnostics only.",
    )


def load_akouo_source(path: Path, condition_slug: str) -> Source:
    payload = json.load(path.open("r", encoding="utf-8"))
    condition = payload["conditions"][condition_slug]
    return Source(
        source_id=f"akouo_reference_{condition_slug}",
        source_role="offline_acoustic_reference_recognizer",
        population=f"Speech Commands X_test fixed noisy condition, {condition['condition']}",
        evidence_type="confusion_matrix_only",
        path=path,
        true_labels=None,
        pred_labels=None,
        confusion_matrix=condition["confusion_matrix"],
        probabilities=None,
        sequence_available=False,
        caveat="Only aggregate confusion matrix is available, so repeated/consecutive action pressure and probability-based no-unknown split cannot be computed.",
    )


def load_embedded_user_study_source(path: Path) -> Source:
    rows = read_csv(path)
    true_labels = [r["intent_ground_truth"].strip().lower() for r in rows]
    pred_labels = [r["predicted_intent"].strip().lower() for r in rows]
    probs = {
        "emergency": [float(r["prob_emergency"]) for r in rows],
        "movement": [float(r["prob_movement"]) for r in rows],
        "unknown": [float(r["prob_unknown"]) for r in rows],
    }
    return Source(
        source_id="embedded_user_study_v4_candidate",
        source_role="embedded_candidate_reinfer_user_study",
        population="User-study v4 participant recordings, desktop TFLite reinference of ESP32 candidate",
        evidence_type="per_sample_probabilities",
        path=path,
        true_labels=true_labels,
        pred_labels=pred_labels,
        confusion_matrix=confusion_from_labels(true_labels, pred_labels),
        probabilities=probs,
        sequence_available=True,
        caveat="This is participant-recording reinference, not the Speech Commands fixed-noisy X_test split; compare as safety-abstraction evidence, not as the offline recognizer leaderboard.",
    )


def support_counts(cm: list[list[int]]) -> dict[str, int]:
    arr = np.asarray(cm, dtype=int)
    return {label: int(arr[i, :].sum()) for i, label in enumerate(LABELS)}


def pred_counts(cm: list[list[int]]) -> dict[str, int]:
    arr = np.asarray(cm, dtype=int)
    return {label: int(arr[:, i].sum()) for i, label in enumerate(LABELS)}


def direct_metrics(source: Source) -> dict[str, Any]:
    cm = np.asarray(source.confusion_matrix, dtype=int)
    n = int(cm.sum())
    e, m, u = 0, 1, 2
    emergency_action_count = int(cm[:, e].sum())
    movement_action_count = int(cm[:, m].sum())
    no_action_count = int(cm[:, u].sum())
    action_count = emergency_action_count + movement_action_count
    false_emergency = int(cm[m, e] + cm[u, e])
    false_movement = int(cm[e, m] + cm[u, m])
    unknown_false_action = int(cm[u, e] + cm[u, m])
    n_unknown = int(cm[u, :].sum())
    n_emergency = int(cm[e, :].sum())
    n_non_emergency = int(n - n_emergency)
    n_non_movement = int(n - cm[m, :].sum())
    missed_emergency = int(cm[e, m] + cm[e, u])

    metrics: dict[str, Any] = {
        "source_id": source.source_id,
        "source_role": source.source_role,
        "population": source.population,
        "evidence_type": source.evidence_type,
        "n_total": n,
        "support": support_counts(source.confusion_matrix),
        "predicted_counts": pred_counts(source.confusion_matrix),
        "emergency_action_count": emergency_action_count,
        "movement_action_count": movement_action_count,
        "no_action_count": no_action_count,
        "total_action_count": action_count,
        "action_pressure_per_100_windows": float(action_count / n * 100.0) if n else None,
        "false_emergency_action_count": false_emergency,
        "false_emergency_action_rate_per_window": float(false_emergency / n) if n else None,
        "false_emergency_action_rate_among_non_emergency": float(false_emergency / n_non_emergency) if n_non_emergency else None,
        "false_movement_action_count": false_movement,
        "false_movement_action_rate_per_window": float(false_movement / n) if n else None,
        "false_movement_action_rate_among_non_movement": float(false_movement / n_non_movement) if n_non_movement else None,
        "unknown_false_action_count": unknown_false_action,
        "unknown_false_action_rate": float(unknown_false_action / n_unknown) if n_unknown else None,
        "unauthorized_movement_action_count": movement_action_count,
        "unauthorized_movement_action_rate_per_window": float(movement_action_count / n) if n else None,
        "missed_emergency_action_count": missed_emergency,
        "missed_emergency_action_rate": float(missed_emergency / n_emergency) if n_emergency else None,
        "confusion_matrix": source.confusion_matrix,
        "sequence_available": source.sequence_available,
        "sequence_caveat": source.caveat if source.sequence_available else "No sequence-level rows available.",
    }
    metrics.update(sequence_metrics(source.pred_labels))
    return metrics


def sequence_metrics(pred_labels: list[str] | None) -> dict[str, Any]:
    if not pred_labels:
        return {
            "consecutive_action_pair_count": None,
            "consecutive_action_pair_rate": None,
            "consecutive_action_pairs_per_100_transitions": None,
            "action_run_count": None,
            "max_consecutive_action_run": None,
            "mean_action_run_length": None,
        }
    action_flags = [label in ACTIONABLE for label in pred_labels]
    pair_count = sum(1 for i in range(1, len(action_flags)) if action_flags[i - 1] and action_flags[i])
    runs = []
    cur = 0
    for flag in action_flags:
        if flag:
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    transitions = max(0, len(action_flags) - 1)
    return {
        "consecutive_action_pair_count": int(pair_count),
        "consecutive_action_pair_rate": float(pair_count / transitions) if transitions else None,
        "consecutive_action_pairs_per_100_transitions": float(pair_count / transitions * 100.0) if transitions else None,
        "action_run_count": int(len(runs)),
        "max_consecutive_action_run": int(max(runs)) if runs else 0,
        "mean_action_run_length": float(np.mean(runs)) if runs else 0.0,
    }


def no_unknown_ablation(source: Source) -> dict[str, Any]:
    cm = np.asarray(source.confusion_matrix, dtype=int)
    n = int(cm.sum())
    e, m, u = 0, 1, 2
    direct = direct_metrics(source)
    n_unknown = int(cm[u, :].sum())

    base: dict[str, Any] = {
        "source_id": source.source_id,
        "source_role": source.source_role,
        "population": source.population,
        "evidence_type": source.evidence_type,
        "n_total": n,
        "n_unknown": n_unknown,
        "original_action_pressure_per_100_windows": direct["action_pressure_per_100_windows"],
        "original_unknown_false_action_rate": direct["unknown_false_action_rate"],
        "method": "",
        "caveat": "",
    }

    if source.probabilities and source.true_labels is not None:
        forced_pred = []
        for pe, pm in zip(source.probabilities["emergency"], source.probabilities["movement"]):
            forced_pred.append("emergency" if pe >= pm else "movement")
        forced_cm = confusion_from_labels(source.true_labels, forced_pred)
        forced_source = Source(
            source_id=source.source_id + "_no_unknown_forced",
            source_role=source.source_role,
            population=source.population,
            evidence_type="probability_forced_two_action",
            path=source.path,
            true_labels=source.true_labels,
            pred_labels=forced_pred,
            confusion_matrix=forced_cm,
            probabilities=None,
            sequence_available=source.sequence_available,
            caveat=source.caveat,
        )
        forced_direct = direct_metrics(forced_source)
        forced_arr = np.asarray(forced_cm, dtype=int)
        base.update(
            {
                "method": "exact_probability_argmax_between_emergency_and_movement",
                "true_unknown_to_emergency_forced_rate": float(forced_arr[u, e] / n_unknown) if n_unknown else None,
                "true_unknown_to_movement_forced_rate": float(forced_arr[u, m] / n_unknown) if n_unknown else None,
                "total_unknown_forced_action_rate": 1.0 if n_unknown else None,
                "additional_action_count_from_removed_unknown": int(direct["no_action_count"]),
                "additional_action_pressure_per_100_windows": float(direct["no_action_count"] / n * 100.0) if n else None,
                "forced_direct_mapping": forced_direct,
                "change_false_emergency_action_count": int(forced_direct["false_emergency_action_count"] - direct["false_emergency_action_count"]),
                "change_false_movement_action_count": int(forced_direct["false_movement_action_count"] - direct["false_movement_action_count"]),
                "caveat": "Exact for this source because per-class probabilities are available.",
            }
        )
        return base

    true_unknown_pred_emergency = int(cm[u, e])
    true_unknown_pred_movement = int(cm[u, m])
    true_unknown_pred_unknown = int(cm[u, u])
    base.update(
        {
            "method": "label_only_bounds",
            "true_unknown_to_emergency_forced_rate": None,
            "true_unknown_to_movement_forced_rate": None,
            "true_unknown_to_emergency_forced_rate_lower_bound": float(true_unknown_pred_emergency / n_unknown) if n_unknown else None,
            "true_unknown_to_emergency_forced_rate_upper_bound": float((true_unknown_pred_emergency + true_unknown_pred_unknown) / n_unknown) if n_unknown else None,
            "true_unknown_to_movement_forced_rate_lower_bound": float(true_unknown_pred_movement / n_unknown) if n_unknown else None,
            "true_unknown_to_movement_forced_rate_upper_bound": float((true_unknown_pred_movement + true_unknown_pred_unknown) / n_unknown) if n_unknown else None,
            "total_unknown_forced_action_rate": 1.0 if n_unknown else None,
            "known_true_unknown_already_actionable_count": int(true_unknown_pred_emergency + true_unknown_pred_movement),
            "ambiguous_true_unknown_no_action_to_forced_action_count": int(true_unknown_pred_unknown),
            "additional_action_count_from_removed_unknown": int(direct["no_action_count"]),
            "additional_action_pressure_per_100_windows": float(direct["no_action_count"] / n * 100.0) if n else None,
            "forced_action_pressure_per_100_windows": 100.0 if n else None,
            "change_false_emergency_action_count": None,
            "change_false_movement_action_count": None,
            "caveat": "Only labels/confusion are available. Total true-unknown forced-action rate is exact under a no-unknown classifier, but emergency-vs-movement split is bounded rather than measured.",
        }
    )
    return base


def write_action_table(path: Path, direct_rows: list[dict[str, Any]], ablation_rows: list[dict[str, Any]]) -> None:
    ab_by_id = {row["source_id"]: row for row in ablation_rows}
    fields = [
        "source_id",
        "source_role",
        "population",
        "evidence_type",
        "n_total",
        "action_pressure_per_100_windows",
        "false_emergency_action_rate_per_window",
        "false_movement_action_rate_per_window",
        "unknown_false_action_rate",
        "unauthorized_movement_action_count",
        "missed_emergency_action_rate",
        "consecutive_action_pairs_per_100_transitions",
        "no_unknown_method",
        "total_unknown_forced_action_rate",
        "true_unknown_to_emergency_forced_rate",
        "true_unknown_to_movement_forced_rate",
        "additional_action_pressure_per_100_windows",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in direct_rows:
            ab = ab_by_id[row["source_id"]]
            out = {
                "source_id": row["source_id"],
                "source_role": row["source_role"],
                "population": row["population"],
                "evidence_type": row["evidence_type"],
                "n_total": row["n_total"],
                "action_pressure_per_100_windows": row["action_pressure_per_100_windows"],
                "false_emergency_action_rate_per_window": row["false_emergency_action_rate_per_window"],
                "false_movement_action_rate_per_window": row["false_movement_action_rate_per_window"],
                "unknown_false_action_rate": row["unknown_false_action_rate"],
                "unauthorized_movement_action_count": row["unauthorized_movement_action_count"],
                "missed_emergency_action_rate": row["missed_emergency_action_rate"],
                "consecutive_action_pairs_per_100_transitions": row["consecutive_action_pairs_per_100_transitions"],
                "no_unknown_method": ab["method"],
                "total_unknown_forced_action_rate": ab["total_unknown_forced_action_rate"],
                "true_unknown_to_emergency_forced_rate": ab.get("true_unknown_to_emergency_forced_rate"),
                "true_unknown_to_movement_forced_rate": ab.get("true_unknown_to_movement_forced_rate"),
                "additional_action_pressure_per_100_windows": ab["additional_action_pressure_per_100_windows"],
            }
            writer.writerow({k: "" if out.get(k) is None else out.get(k) for k in fields})


def write_result_tree(output_dir: Path) -> None:
    lines = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            lines.append(f"{rel(path)}\t{path.stat().st_size} bytes")
    (output_dir / "result_tree.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(output_dir: Path, direct_rows: list[dict[str, Any]], ablation_rows: list[dict[str, Any]]) -> None:
    def fmt(x: Any) -> str:
        if x is None:
            return "NA"
        if isinstance(x, float):
            return f"{x:.4f}"
        return str(x)

    lines = [
        "# Safety-State Abstraction Ablations",
        "",
        "This is an offline/action-simulation analysis. It does not run a drone, validate flight safety, train models, or modify the paper.",
        "",
        "## Direct Mapping Summary",
        "",
        "| Source | n | Action pressure / 100 windows | Unknown false action rate | Missed emergency action rate | Unauthorized movement actions |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in direct_rows:
        lines.append(
            f"| {row['source_id']} | {row['n_total']} | {fmt(row['action_pressure_per_100_windows'])} | "
            f"{fmt(row['unknown_false_action_rate'])} | {fmt(row['missed_emergency_action_rate'])} | "
            f"{row['unauthorized_movement_action_count']} |"
        )

    lines.extend(
        [
            "",
            "## No-Unknown Ablation Summary",
            "",
            "| Source | Method | True unknown forced action rate | Additional action pressure / 100 windows | Caveat |",
            "|---|---|---:|---:|---|",
        ]
    )
    for row in ablation_rows:
        lines.append(
            f"| {row['source_id']} | {row['method']} | {fmt(row['total_unknown_forced_action_rate'])} | "
            f"{fmt(row['additional_action_pressure_per_100_windows'])} | {row['caveat']} |"
        )

    lines.extend(
        [
            "",
            "## Paper Boundary",
            "",
            "Paper-usable as evidence that direct label-to-action mapping creates action pressure and that the unknown/fallback state is a containment mechanism. Do not describe these numbers as flight validation or as measured UAV actuation.",
            "",
            "## Result Tree",
            "",
            "See `result_tree.txt`.",
            "",
        ]
    )
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="weeklyresult/weekly_drone_2026w23/safety_ablation_direct_mapping_20260604")
    parser.add_argument("--asr-parsed", default="weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/parsed_intents.csv")
    parser.add_argument("--akouo-confusion", default="weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603/confusion_matrices.json")
    parser.add_argument("--akouo-condition", default="snr_m10db")
    parser.add_argument("--embedded-trials", default="weeklyresult/weekly_drone_2026w23/user_study_v4_esp32_candidate_reinfer_20260604_121452/trial_predictions.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = abs_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources: list[Source] = []
    unavailable = []

    for loader, raw_path, kwargs in [
        (load_akouo_source, args.akouo_confusion, {"condition_slug": args.akouo_condition}),
        (load_asr_source, args.asr_parsed, {}),
        (load_embedded_user_study_source, args.embedded_trials, {}),
    ]:
        path = abs_path(raw_path)
        if path.exists():
            if loader is load_akouo_source:
                sources.append(loader(path, **kwargs))
            else:
                sources.append(loader(path))
        else:
            unavailable.append({"path": rel(path), "reason": "not_found"})

    unavailable.append(
        {
            "source_id": "compact_classifier_baselines",
            "reason": "No compact-baseline per-sample predictions found in the current main worktree; existing paper rows are aggregate first-batch metrics only.",
        }
    )

    direct_rows = [direct_metrics(src) for src in sources]
    ablation_rows = [no_unknown_ablation(src) for src in sources]

    input_sources = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "included_sources": [
            {
                "source_id": src.source_id,
                "source_role": src.source_role,
                "population": src.population,
                "evidence_type": src.evidence_type,
                "path": rel(src.path),
                "sequence_available": src.sequence_available,
                "has_probabilities": src.probabilities is not None,
                "caveat": src.caveat,
            }
            for src in sources
        ],
        "unavailable_sources": unavailable,
    }

    run_manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "repo": {
            "branch": run_git(["branch", "--show-current"]),
            "head": run_git(["rev-parse", "HEAD"]),
            "status_short_branch": run_git(["status", "--short", "--branch"]).splitlines(),
        },
        "command": {
            "argv": sys.argv,
            "shell_command": shell_command(),
        },
        "policy": {
            "emergency_prediction": "emergency action",
            "movement_prediction": "movement action",
            "unknown_prediction": "no action",
            "bridge": "disabled in simulator",
            "manual_override": "absent in simulator",
            "policy_gate": "absent in simulator",
        },
        "metrics_definition": {
            "action_pressure_per_100_windows": "(predicted emergency + predicted movement) / total_windows * 100",
            "unknown_false_action_rate": "among true unknown windows, fraction predicted emergency or movement",
            "unauthorized_movement_action_count": "all movement actions under the no-bridge/no-authority simulator",
            "missed_emergency_action_rate": "among true emergency windows, fraction not mapped to emergency action",
        },
        "outputs": {
            "run_manifest": rel(output_dir / "run_manifest.json"),
            "input_sources": rel(output_dir / "input_sources.json"),
            "direct_mapping_metrics": rel(output_dir / "direct_mapping_metrics.json"),
            "no_unknown_ablation_metrics": rel(output_dir / "no_unknown_ablation_metrics.json"),
            "action_pressure_table": rel(output_dir / "action_pressure_table.csv"),
            "report": rel(output_dir / "report.md"),
            "result_tree": rel(output_dir / "result_tree.txt"),
        },
    }

    json_dump(output_dir / "run_manifest.json", run_manifest)
    json_dump(output_dir / "input_sources.json", input_sources)
    json_dump(output_dir / "direct_mapping_metrics.json", {"sources": direct_rows})
    json_dump(output_dir / "no_unknown_ablation_metrics.json", {"sources": ablation_rows})
    write_action_table(output_dir / "action_pressure_table.csv", direct_rows, ablation_rows)
    write_report(output_dir, direct_rows, ablation_rows)
    write_result_tree(output_dir)

    print(f"[done] wrote {rel(output_dir)}")
    for row in direct_rows:
        print(
            f"{row['source_id']}: action_pressure={row['action_pressure_per_100_windows']:.2f}/100, "
            f"unknown_false_action={row['unknown_false_action_rate']:.4f}, "
            f"missed_emergency={row['missed_emergency_action_rate']:.4f}"
        )


if __name__ == "__main__":
    main()
