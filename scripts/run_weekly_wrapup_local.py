#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FINETUNE_SCRIPT = os.path.join(ROOT, "scripts", "run_finetune_logmel_kd.py")


@dataclass
class Setting:
    setting: str
    ckpt: str
    category: str
    notes: str


def _as_abs(path: str) -> str:
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(ROOT, path))


def _read_summary_csv(path: str) -> Dict[str, float]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
    return {
        "acc_original": float(row["acc_original"]),
        "acc_finetuned": float(row["acc_finetuned"]),
        "delta_acc": float(row["acc_delta"]),
    }


def _parse_classification_report(path: str) -> Dict[str, Dict[str, float]]:
    metrics: Dict[str, Dict[str, float]] = {}
    pattern = re.compile(r"^\s*(emergency|movement|unknown)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s*$")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = pattern.match(line)
            if not m:
                continue
            cls = m.group(1)
            metrics[cls] = {
                "precision": float(m.group(2)),
                "recall": float(m.group(3)),
                "f1": float(m.group(4)),
                "support": float(m.group(5)),
            }
    return metrics


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _run_finetune(
    setting: Setting,
    output_dir: str,
    finetuned_ckpt: str,
    testset: str,
    encoder: str,
    split_cache: str,
    finetune_ratio: float,
    val_ratio: float,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
) -> None:
    cmd = [
        sys.executable,
        FINETUNE_SCRIPT,
        "--testset",
        testset,
        "--encoder",
        encoder,
        "--weights",
        setting.ckpt,
        "--finetuned-weights",
        finetuned_ckpt,
        "--output",
        output_dir,
        "--split-cache",
        split_cache,
        "--finetune-ratio",
        str(finetune_ratio),
        "--val-ratio",
        str(val_ratio),
        "--epochs",
        str(epochs),
        "--batch-size",
        str(batch_size),
        "--lr",
        str(lr),
        "--seed",
        str(seed),
    ]
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    env.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
    env.setdefault("TF_DETERMINISTIC_OPS", "1")
    env.setdefault("PYTHONHASHSEED", str(seed))
    subprocess.run(cmd, check=True, cwd=ROOT, env=env)


def _to_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def _safe_metric(metrics: Dict[str, Dict[str, float]], cls: str, field: str) -> float:
    return float(metrics.get(cls, {}).get(field, 0.0))


def build_settings(weekly_tag: str) -> Tuple[List[Setting], List[str]]:
    base = f"saved_models/weekly_{weekly_tag}"
    completed = [
        Setting("best_embed_kd", _as_abs(f"{base}/baseline/best_embed_kd/student_kd_best.weights.h5"), "baseline", "embed-only baseline"),
        Setting("ablation_exp_A", _as_abs(f"{base}/ablation/exp_A/student_kd_best.weights.h5"), "ablation", "A: no KD, no emergency aug"),
        Setting("ablation_exp_B", _as_abs(f"{base}/ablation/exp_B/student_kd_best.weights.h5"), "ablation", "B: embed KD only"),
        Setting("ablation_exp_C", _as_abs(f"{base}/ablation/exp_C/student_kd_best.weights.h5"), "ablation", "C: emergency aug only"),
        Setting("ablation_exp_D", _as_abs(f"{base}/ablation/exp_D/student_kd_best.weights.h5"), "ablation", "D: embed KD + emergency aug"),
        Setting("prewarm_direct_noisy", _as_abs(f"{base}/prewarm/direct_noisy/student_kd_best.weights.h5"), "prewarm", "direct noisy"),
        Setting("prewarm_clean_then_noisy", _as_abs(f"{base}/prewarm/prewarm_clean_then_noisy/student_kd_best.weights.h5"), "prewarm", "clean prewarm then noisy"),
        Setting("logits_only", _as_abs(f"{base}/logits_recheck/logits_only/student_kd_best.weights.h5"), "logits", "logits-only (alpha=0)"),
    ]
    pending = [
        "logits_recheck/ce_plus_logits",
        "logits_recheck/embed_only_reference",
    ]
    return completed, pending


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly-tag", default="drone_2026w13")
    parser.add_argument("--testset", default="/Users/zilongzeng/Research/Drone/testset")
    parser.add_argument("--encoder", default="saved_models/label_encoder.joblib")
    parser.add_argument("--output-root", default="result/weekly_wrapup_2026w13")
    parser.add_argument("--split-cache", default="result/weekly_wrapup_2026w13/split_indices_testset.npz")
    parser.add_argument("--finetune-ratio", type=float, default=0.3)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--repro-check-setting", default="best_embed_kd")
    args = parser.parse_args()

    output_root = _as_abs(args.output_root)
    split_cache = _as_abs(args.split_cache)
    testset = _as_abs(args.testset)
    encoder = _as_abs(args.encoder)

    os.makedirs(output_root, exist_ok=True)
    os.makedirs(os.path.dirname(split_cache), exist_ok=True)

    completed_settings, pending_settings = build_settings(args.weekly_tag)

    missing = [s.setting for s in completed_settings if not os.path.exists(s.ckpt)]
    if missing:
        raise FileNotFoundError(f"Missing completed checkpoints: {missing}")

    class_counts = {}
    for cls in sorted(d for d in os.listdir(testset) if os.path.isdir(os.path.join(testset, d))):
        count = 0
        cls_dir = os.path.join(testset, cls)
        for dp, _, files in os.walk(cls_dir):
            count += sum(1 for fn in files if fn.lower().endswith(".wav"))
        class_counts[cls] = count

    rows_main: List[Dict[str, float]] = []
    per_setting_artifacts = {}

    for s in completed_settings:
        out_dir = os.path.join(output_root, "finetune", s.setting)
        finetuned_ckpt = os.path.join(output_root, "finetuned_ckpts", f"{s.setting}.weights.h5")
        os.makedirs(os.path.dirname(finetuned_ckpt), exist_ok=True)
        _run_finetune(
            setting=s,
            output_dir=out_dir,
            finetuned_ckpt=finetuned_ckpt,
            testset=testset,
            encoder=encoder,
            split_cache=split_cache,
            finetune_ratio=args.finetune_ratio,
            val_ratio=args.val_ratio,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            seed=args.seed,
        )

        summary = _read_summary_csv(os.path.join(out_dir, "summary.csv"))
        cls_metrics = _parse_classification_report(os.path.join(out_dir, "finetuned", "classification_report.txt"))
        row = {
            "setting": s.setting,
            "acc_original": summary["acc_original"],
            "acc_finetuned": summary["acc_finetuned"],
            "delta_acc": summary["delta_acc"],
            "emergency_recall_ft": _safe_metric(cls_metrics, "emergency", "recall"),
            "emergency_f1_ft": _safe_metric(cls_metrics, "emergency", "f1"),
            "movement_recall_ft": _safe_metric(cls_metrics, "movement", "recall"),
            "unknown_recall_ft": _safe_metric(cls_metrics, "unknown", "recall"),
        }
        rows_main.append(row)
        per_setting_artifacts[s.setting] = {
            "output_dir": out_dir,
            "report": os.path.join(out_dir, "finetuned", "classification_report.txt"),
            "confusion_matrix": os.path.join(out_dir, "finetuned", "confusion_matrix.png"),
            "summary_csv": os.path.join(out_dir, "summary.csv"),
            "finetuned_ckpt": finetuned_ckpt,
            "source_ckpt": s.ckpt,
            "category": s.category,
            "notes": s.notes,
        }

    rows_main.sort(key=lambda x: x["acc_finetuned"], reverse=True)

    # Main comparison table
    main_csv = os.path.join(output_root, "comparison_main.csv")
    with open(main_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "setting",
                "acc_original",
                "acc_finetuned",
                "delta_acc",
                "emergency_recall_ft",
                "emergency_f1_ft",
                "movement_recall_ft",
                "unknown_recall_ft",
            ],
        )
        w.writeheader()
        for r in rows_main:
            w.writerow(r)

    # Interpretation slices
    idx = {r["setting"]: r for r in rows_main}
    slices = []
    # Ablation effects
    A, B, C, D = idx["ablation_exp_A"], idx["ablation_exp_B"], idx["ablation_exp_C"], idx["ablation_exp_D"]
    slices.append(("ablation", "kd_effect_acc", B["acc_finetuned"] - A["acc_finetuned"], "B - A"))
    slices.append(("ablation", "aug_effect_acc", C["acc_finetuned"] - A["acc_finetuned"], "C - A"))
    slices.append(("ablation", "joint_effect_acc", D["acc_finetuned"] - A["acc_finetuned"], "D - A"))
    slices.append(("ablation", "interaction_acc", D["acc_finetuned"] - B["acc_finetuned"] - C["acc_finetuned"] + A["acc_finetuned"], "D - B - C + A"))

    # Prewarm
    P0, P1 = idx["prewarm_direct_noisy"], idx["prewarm_clean_then_noisy"]
    slices.append(("prewarm", "prewarm_gain_acc", P1["acc_finetuned"] - P0["acc_finetuned"], "prewarm - direct"))
    slices.append(("prewarm", "prewarm_gain_emergency_f1", P1["emergency_f1_ft"] - P0["emergency_f1_ft"], "prewarm - direct"))

    # Logits vs embed references (completed only)
    L = idx["logits_only"]
    Eref = idx["best_embed_kd"]
    Bemb = idx["ablation_exp_B"]
    slices.append(("logits_vs_embed", "logits_minus_best_embed_acc", L["acc_finetuned"] - Eref["acc_finetuned"], "logits_only - best_embed_kd"))
    slices.append(("logits_vs_embed", "logits_minus_embed_only_acc", L["acc_finetuned"] - Bemb["acc_finetuned"], "logits_only - ablation_exp_B"))
    slices.append(("logits_vs_embed", "logits_minus_best_embed_emergency_f1", L["emergency_f1_ft"] - Eref["emergency_f1_ft"], "logits_only - best_embed_kd"))

    slices_csv = os.path.join(output_root, "interpretation_slices.csv")
    with open(slices_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["slice_group", "metric", "value", "definition"])
        for row in slices:
            w.writerow([row[0], row[1], f"{row[2]:.6f}", row[3]])

    # Reproducibility check: rerun one setting with same split cache
    repro_setting = args.repro_check_setting
    repro = {"setting": repro_setting, "status": "skipped"}
    if repro_setting in per_setting_artifacts:
        before_hash = _file_sha256(split_cache) if os.path.exists(split_cache) else None
        s = next(ss for ss in completed_settings if ss.setting == repro_setting)
        out_dir_repeat = os.path.join(output_root, "finetune_repeat", s.setting)
        finetuned_ckpt_repeat = os.path.join(output_root, "finetuned_ckpts_repeat", f"{s.setting}.weights.h5")
        os.makedirs(os.path.dirname(finetuned_ckpt_repeat), exist_ok=True)
        _run_finetune(
            setting=s,
            output_dir=out_dir_repeat,
            finetuned_ckpt=finetuned_ckpt_repeat,
            testset=testset,
            encoder=encoder,
            split_cache=split_cache,
            finetune_ratio=args.finetune_ratio,
            val_ratio=args.val_ratio,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            seed=args.seed,
        )
        first = _read_summary_csv(per_setting_artifacts[s.setting]["summary_csv"])
        second = _read_summary_csv(os.path.join(out_dir_repeat, "summary.csv"))
        after_hash = _file_sha256(split_cache) if os.path.exists(split_cache) else None
        repro = {
            "setting": s.setting,
            "status": "done",
            "split_cache_hash_before": before_hash,
            "split_cache_hash_after": after_hash,
            "split_cache_stable": before_hash == after_hash,
            "acc_original_first": first["acc_original"],
            "acc_original_repeat": second["acc_original"],
            "acc_finetuned_first": first["acc_finetuned"],
            "acc_finetuned_repeat": second["acc_finetuned"],
            "delta_acc_repeat_minus_first": second["acc_finetuned"] - first["acc_finetuned"],
        }

    with open(os.path.join(output_root, "reproducibility_check.json"), "w", encoding="utf-8") as f:
        json.dump(repro, f, indent=2, ensure_ascii=True)

    with open(os.path.join(output_root, "artifacts_index.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "weekly_tag": args.weekly_tag,
                "testset": testset,
                "class_counts": class_counts,
                "completed_settings": [s.setting for s in completed_settings],
                "pending_settings_ignored": pending_settings,
                "artifacts": per_setting_artifacts,
                "tables": {
                    "comparison_main_csv": main_csv,
                    "interpretation_slices_csv": slices_csv,
                },
            },
            f,
            indent=2,
            ensure_ascii=True,
        )

    # Weekly report
    best = rows_main[0]
    md_main = _to_markdown_table(
        [
            "setting",
            "acc_original",
            "acc_finetuned",
            "delta_acc",
            "emergency_recall_ft",
            "emergency_f1_ft",
            "movement_recall_ft",
            "unknown_recall_ft",
        ],
        [
            [
                r["setting"],
                f"{r['acc_original']:.4f}",
                f"{r['acc_finetuned']:.4f}",
                f"{r['delta_acc']:+.4f}",
                f"{r['emergency_recall_ft']:.4f}",
                f"{r['emergency_f1_ft']:.4f}",
                f"{r['movement_recall_ft']:.4f}",
                f"{r['unknown_recall_ft']:.4f}",
            ]
            for r in rows_main
        ],
    )
    md_slices = _to_markdown_table(
        ["slice_group", "metric", "value", "definition"],
        [[g, m, f"{v:+.4f}", d] for g, m, v, d in slices],
    )

    report_suffix = args.weekly_tag
    if report_suffix.startswith("drone_"):
        report_suffix = report_suffix[len("drone_"):]
    report_suffix = report_suffix.replace("/", "_")
    report_path = os.path.join(output_root, f"weekly_report_{report_suffix}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Weekly Report ({report_suffix}): Local Finetune + Analysis\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- Evaluation dataset: `{testset}` with class counts {class_counts}.\n")
        f.write(f"- Included completed settings: {[s.setting for s in completed_settings]}.\n")
        f.write(f"- Best finetuned accuracy this week: `{best['setting']}` at `{best['acc_finetuned']:.4f}`.\n")
        f.write("- Unfinished settings were excluded from quantitative ranking and documented as pending.\n")
        f.write("- Local finetune used one fixed split cache across all settings for comparability.\n\n")

        f.write("## Main Results Table\n\n")
        f.write(md_main + "\n\n")
        f.write(f"Source CSV: `{main_csv}`\n\n")

        f.write("## Interpretation Slices\n\n")
        f.write(md_slices + "\n\n")
        f.write(f"Source CSV: `{slices_csv}`\n\n")

        f.write("## Ignored This Week (Pending Experiments)\n\n")
        for p in pending_settings:
            f.write(f"- `{p}` (excluded from ranking and inference this week)\n")
        f.write("\nImpact statement:\n")
        f.write("- Logits branch conclusions remain provisional until `ce_plus_logits` and `embed_only_reference` are completed.\n\n")

        f.write("## Oral Talking Outline (Meeting)\n\n")
        outline = [
            "We completed local finetune/evaluation on the independent local testset using all completed 2026w13 checkpoints.",
            "We kept one shared split cache across settings to maintain controlled comparisons.",
            "The best-performing completed setting by finetuned accuracy was highlighted in the main table.",
            "Ablation decomposition shows separate and joint effects of embedding KD and emergency-only augmentation.",
            "Prewarm vs direct-noisy comparison was quantified on both accuracy and emergency F1.",
            "Logits-only was compared against completed embed-centric references; unfinished logits settings were intentionally excluded.",
            "Two pending experiments are the main uncertainty for final logits conclusions.",
            "Next week priority is to finish pending logits runs, then rerun consolidated ranking and refresh narrative conclusions.",
        ]
        for i, bullet in enumerate(outline, 1):
            f.write(f"{i}. {bullet}\n")
        f.write("\n")

        f.write("## Next-Step Plan (Prioritized)\n\n")
        next_steps = [
            "Finish `logits_recheck/ce_plus_logits` and `logits_recheck/embed_only_reference` with the same local split cache.",
            "Regenerate the same two tables and update rankings including completed logits branch.",
            "Run one extra seed for top-2 settings to validate stability of weekly headline claims.",
            "Add no-unknown slice analysis for emergency/movement decision boundary behavior.",
            "Prepare publish-ready figure bundle (confusion matrices + key metrics table) for advisor review.",
        ]
        for i, bullet in enumerate(next_steps, 1):
            f.write(f"{i}. {bullet}\n")
        f.write("\n")

        f.write("## Reproducibility Check\n\n")
        f.write(f"```json\n{json.dumps(repro, indent=2, ensure_ascii=True)}\n```\n")

    print(f"Saved: {main_csv}")
    print(f"Saved: {slices_csv}")
    print(f"Saved: {report_path}")
    print(f"Saved: {os.path.join(output_root, 'reproducibility_check.json')}")
    print(f"Saved: {os.path.join(output_root, 'artifacts_index.json')}")


if __name__ == "__main__":
    main()
