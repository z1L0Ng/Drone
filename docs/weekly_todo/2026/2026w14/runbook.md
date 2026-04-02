# Weekly Runbook (Drone 2026w14)

## 1) Server Training

```bash
# train all planned stages
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh all
```

Optional staged execution:

```bash
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh baseline
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh ablation
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh prewarm
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh logits
```

## 2) Local Evaluation + Summaries

```bash
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_local_eval.sh
```

## 3) Weekly Wrap-up (Local)

```bash
conda run -n drone python scripts/run_weekly_wrapup_local.py
```

## 4) Handoff Steps
1. Update `docs/weekly_todo/2026/2026w14/todo.md`.
2. Append a row to `docs/weekly_todo/handoff_log.md`.
3. Record exact command + output path + next owner/action.
