# Full Cleanup Manifest (Week Reset)

- Date: 2026-04-02
- Batch: `archive/full_cleanup_for_2026w14_20260402_135839`
- Intent: fully retire `2026w13` assets and reset repo to a clean, usable `2026w14` state.

## What Was Archived
See `moved_paths.txt` for exact source paths.

Main categories:
- Previous-week docs (`docs/weekly_todo/2026/2026w13`, old `handoff_log.md`)
- Previous-week results (`result/weekly_drone_2026w13`, `result/weekly_wrapup_2026w13`)
- Previous-week checkpoints (`saved_models/weekly_drone_2026w13`)
- Previous-week analysis and experiment summaries (`analysis/cross_language_emergency/*`, `experiments/*`)

## Current Active Baseline (Local + Server)
- `docs/weekly_todo/2026/2026w14/`
- `docs/weekly_todo/handoff_log.md`
- `docs/technical_spec/`
- `docs/overleaf/`
- `scripts/`, `src/`, `config/`
- `experiments/`, `analysis/`, `result/`, `logs/`, `notebooks/` (reset for current week)
- `dataset/`, `testset/`, `saved_models/label_encoder.joblib`

## Restore (If Needed)
Run from repo root:

```bash
while IFS= read -r p; do
  src="archive/full_cleanup_for_2026w14_20260402_135839/$p"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$p")"
    mv "$src" "$p"
  fi
done < archive/full_cleanup_for_2026w14_20260402_135839/moved_paths.txt
```
