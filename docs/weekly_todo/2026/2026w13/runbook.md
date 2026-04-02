# Weekly Runbook (Drone 2026w13)

## 1) Server Training

```bash
# train all (baseline + ablation + prewarm + logits)
WEEKLY_TAG=drone_2026w13 bash scripts/run_weekly_server_train.sh all

# or split by stage
WEEKLY_TAG=drone_2026w13 bash scripts/run_weekly_server_train.sh baseline
WEEKLY_TAG=drone_2026w13 bash scripts/run_weekly_server_train.sh ablation
WEEKLY_TAG=drone_2026w13 bash scripts/run_weekly_server_train.sh prewarm
WEEKLY_TAG=drone_2026w13 bash scripts/run_weekly_server_train.sh logits
```

## 2) Local Evaluation + Summaries

```bash
WEEKLY_TAG=drone_2026w13 bash scripts/run_weekly_local_eval.sh
```

If checkpoints are in non-default paths, pass overrides:

```bash
BASELINE_CKPT=/abs/path/to/best.ckpt \
ABLAT_A_CKPT=/abs/path/to/expA.ckpt \
ABLAT_B_CKPT=/abs/path/to/expB.ckpt \
ABLAT_C_CKPT=/abs/path/to/expC.ckpt \
ABLAT_D_CKPT=/abs/path/to/expD.ckpt \
WEEKLY_TAG=drone_2026w13 \
bash scripts/run_weekly_local_eval.sh
```

## 3) Cross-language Analysis (Local)

```bash
python scripts/standardize_cross_language_audio.py \
  --input-root local_data/cross_language \
  --output-root analysis/cross_language_emergency/standardized \
  --metadata analysis/cross_language_emergency/standardized_metadata.csv

python scripts/analyze_cross_language_emergency.py \
  --input-root analysis/cross_language_emergency/standardized \
  --output-root analysis/cross_language_emergency
```

## 4) Handoff Steps
1. Update `docs/weekly_todo/2026/2026w13/todo.md`.
2. Append a row to `docs/weekly_todo/handoff_log.md`.
3. Record exact command + output path + next owner/action.
