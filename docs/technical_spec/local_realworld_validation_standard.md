# Local Real-World Validation Standard (Drone)

## Goal
- Establish a repeatable local validation stage on manually collected real-world data (`testset/`).
- Make this stage mandatory after weekly server training sync and before multilingual expansion decisions.

## Scope
- Local only.
- Inputs:
  - weekly model checkpoints (baseline + weekly candidates)
  - local `testset/` in class-folder format (`emergency/`, `movement/`, `unknown/`)
- Outputs:
  - inference-only metrics
  - finetune+inference metrics
  - delta summary used for model adoption decisions

## Standard workflow
1. Inference-only validation:
   - script: `scripts/eval_logmel_kd_checkpoint.py`
   - run on all weekly candidates with same testset.
2. Finetune validation:
   - script: `scripts/run_finetune_logmel_kd.py`
   - use same split cache across models (`split_indices_testset.npz`).
3. Comparison and decision:
   - compare original vs finetuned metrics.
   - focus on emergency recall/F1 and overall accuracy.
4. Handoff:
   - append to `docs/weekly_todo/handoff_log.md`
   - summarize in weekly wrap-up docs.

## Required output layout
- `result/weekly_wrapup_<week>/local_realworld_eval/<model>/...`
- `result/weekly_wrapup_<week>/local_realworld_finetune/<model>/...`

Minimum files per model:
- inference-only:
  - `metrics.json`
  - `classification_report.txt`
  - `confusion_matrix.png`
- finetune:
  - `summary.csv`
  - `original/classification_report.txt`
  - `finetuned/classification_report.txt`
  - `finetuned/confusion_matrix.png`

## Data growth policy
- Keep adding local manually collected samples each week.
- Track dataset version and sample counts per class in weekly wrap-up.
- When data schema changes (new labels/noise conditions), update mapping notes before running comparisons.

## Decision rule
- Adopt candidate only when:
  - server-side weekly metrics are not regressing baseline, and
  - local real-world inference-only is at least baseline-level, and
  - finetune gain is stable (no severe class collapse).
- Defer candidate when:
  - emergency recall/F1 regresses significantly on local real-world testset.
