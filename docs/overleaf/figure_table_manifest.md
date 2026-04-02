# Figure/Table Manifest

Track which result artifact is used in Overleaf and whether it is final.

| ID | Type | Overleaf Caption (Draft) | Source Path | Script/Command | Status |
|---|---|---|---|---|---|
| F1 | Figure | Main comparison across completed settings | `result/weekly_wrapup_2026w13/comparison_main.csv` | `conda run -n drone python scripts/run_weekly_wrapup_local.py` | draft |
| F2 | Figure | Cross-language emergency analysis | `analysis/cross_language_emergency/` | `python scripts/analyze_cross_language_emergency.py ...` | draft |
| T1 | Table | Weekly interpretation slices | `result/weekly_wrapup_2026w13/interpretation_slices.csv` | `conda run -n drone python scripts/run_weekly_wrapup_local.py` | draft |
