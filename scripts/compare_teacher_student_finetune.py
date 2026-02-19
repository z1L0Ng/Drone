#!/usr/bin/env python3

import os
import csv
import re

ROOT = "/Users/zilongzeng/Research/Drone"

PATHS = {
    "student": {
        "summary": os.path.join(ROOT, "result/finetune/logmel_kd/summary.csv"),
        "original_report": os.path.join(ROOT, "result/finetune/logmel_kd/original/classification_report.txt"),
        "finetuned_report": os.path.join(ROOT, "result/finetune/logmel_kd/finetuned/classification_report.txt"),
    },
    "teacher": {
        "summary": os.path.join(ROOT, "result/finetune/logmel_kd_teacher/summary.csv"),
        "original_report": os.path.join(ROOT, "result/finetune/logmel_kd_teacher/original/classification_report.txt"),
        "finetuned_report": os.path.join(ROOT, "result/finetune/logmel_kd_teacher/finetuned/classification_report.txt"),
    },
}

OUT_DIR = os.path.join(ROOT, "result/finetune/teacher_student_compare")
os.makedirs(OUT_DIR, exist_ok=True)


def read_summary(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
    return {
        "acc_original": float(row["acc_original"]),
        "acc_finetuned": float(row["acc_finetuned"]),
        "acc_delta": float(row["acc_delta"]),
    }


def read_report(path):
    metrics = {}
    acc = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            m_acc = re.match(r"^Accuracy:\s*([0-9.]+)$", line)
            if m_acc:
                acc = float(m_acc.group(1))
                continue

            # example: emergency     0.7500    0.7337    0.7418       184
            m_cls = re.match(r"^(emergency|movement|unknown)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)$", line)
            if m_cls:
                cls = m_cls.group(1)
                metrics[cls] = {
                    "precision": float(m_cls.group(2)),
                    "recall": float(m_cls.group(3)),
                    "f1": float(m_cls.group(4)),
                    "support": int(m_cls.group(5)),
                }
    return acc, metrics


def main():
    rows = []
    cls_rows = []

    for model_name, p in PATHS.items():
        s = read_summary(p["summary"])
        o_acc, o_metrics = read_report(p["original_report"])
        f_acc, f_metrics = read_report(p["finetuned_report"])

        rows.append([
            model_name,
            f"{s['acc_original']:.4f}",
            f"{s['acc_finetuned']:.4f}",
            f"{s['acc_delta']:+.4f}",
            f"{o_acc:.4f}" if o_acc is not None else "",
            f"{f_acc:.4f}" if f_acc is not None else "",
        ])

        for cls in ["emergency", "movement", "unknown"]:
            om = o_metrics.get(cls, {})
            fm = f_metrics.get(cls, {})
            cls_rows.append([
                model_name,
                cls,
                f"{om.get('precision', float('nan')):.4f}",
                f"{om.get('recall', float('nan')):.4f}",
                f"{om.get('f1', float('nan')):.4f}",
                f"{fm.get('precision', float('nan')):.4f}",
                f"{fm.get('recall', float('nan')):.4f}",
                f"{fm.get('f1', float('nan')):.4f}",
                f"{(fm.get('recall', float('nan')) - om.get('recall', float('nan'))):+.4f}",
                f"{(fm.get('f1', float('nan')) - om.get('f1', float('nan'))):+.4f}",
            ])

    summary_csv = os.path.join(OUT_DIR, "summary_compare.csv")
    with open(summary_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "acc_original", "acc_finetuned", "acc_delta", "report_acc_original", "report_acc_finetuned"])
        w.writerows(rows)

    class_csv = os.path.join(OUT_DIR, "classwise_compare.csv")
    with open(class_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "model", "class",
            "orig_precision", "orig_recall", "orig_f1",
            "ft_precision", "ft_recall", "ft_f1",
            "delta_recall", "delta_f1",
        ])
        w.writerows(cls_rows)

    md_path = os.path.join(OUT_DIR, "comparison.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Teacher vs Student Finetune Comparison\n\n")
        f.write("## Overall\n\n")
        f.write("| model | acc_original | acc_finetuned | acc_delta |\n")
        f.write("|---|---:|---:|---:|\n")
        for r in rows:
            f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |\n")

        f.write("\n## Class-wise (Recall/F1)\n\n")
        f.write("| model | class | orig_recall | ft_recall | delta_recall | orig_f1 | ft_f1 | delta_f1 |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")
        for r in cls_rows:
            f.write(f"| {r[0]} | {r[1]} | {r[3]} | {r[6]} | {r[8]} | {r[4]} | {r[7]} | {r[9]} |\n")

    print(f"Saved: {summary_csv}")
    print(f"Saved: {class_csv}")
    print(f"Saved: {md_path}")


if __name__ == "__main__":
    main()
