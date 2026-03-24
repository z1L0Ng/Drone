# Drone Handoff Log (WEEKLY_TAG=drone_2026w13)

## Purpose
- Keep local coding/evaluation and server training synchronized.
- Every handoff must have one row below.

## Required Fields
| Time | Side | Commit | Command | Outputs | Next | Risk |
|---|---|---|---|---|---|---|

## Handoff Checklist
1. Run `git status` and confirm only expected files are changed.
2. Update `TODO_THIS_WEEK.md` with the day status.
3. Append one row in this file with exact commands and output paths.
4. If training is running, include PID/log path.
5. If blocked, include explicit blocker and owner.

## Entries
| Time | Side | Commit | Command | Outputs | Next | Risk |
|---|---|---|---|---|---|---|
| 2026-03-23 15:00 PDT | local | pending | bootstrap weekly workflow scripts and docs | `docs/`, `scripts/`, `experiments/` scaffolding | run server weekly training script | none |
| 2026-03-23 21:05 PDT | local | working-tree (uncommitted) | `bash scripts/run_weekly_local_eval.sh`; `python scripts/standardize_cross_language_audio.py`; `python scripts/analyze_cross_language_emergency.py` | `experiments/*` pending summaries + `analysis/cross_language_emergency/*` plots/findings | run server training then rerun local eval with real checkpoints | local env lacks TensorFlow for checkpoint eval |
