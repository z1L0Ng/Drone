# Focus Cleanup Manifest

- Date: 2026-04-02
- Batch: `archive/focus_cleanup_20260402_135700`
- Goal: Keep repo clean and usable for current weekly focus while preserving old artifacts.

## Active Focus Kept (Local + Server)
- `docs/weekly_todo/`
- `docs/technical_spec/`
- `docs/overleaf/`
- `experiments/`
- `analysis/cross_language_emergency/`
- `saved_models/weekly_drone_2026w13/`
- `result/weekly_drone_2026w13/`
- `result/weekly_wrapup_2026w13/` (report + lightweight finetune outputs)
- `scripts/`, `src/`, `config/`, `dataset/`, `testset/`

## Archived in This Batch
See `moved_paths.txt` for exact original paths.

## Why These Were Archived
- Historical model checkpoints and intermediate outputs not in current weekly focus.
- Legacy finetune/inference outputs with high storage cost and low immediate usage.
- Old logs and notebook not needed for current server/local loop.

## Restore (If Needed)
Run from repo root:

```bash
while IFS= read -r p; do
  src="archive/focus_cleanup_20260402_135700/$p"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$p")"
    mv "$src" "$p"
  fi
done < archive/focus_cleanup_20260402_135700/moved_paths.txt
```
