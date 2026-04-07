# Changelog Phase 1.2

- Added real scanned counts from isolated CREMA-D audio staged at `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/crema_d`.
- Updated `sample_count_table_2026w14.csv` with `count_source=scanned` rows showing non-zero no-surprise counts for CREMA-D and combined plan:
  - CREMA-D scanned (no-surprise): emergency=667, normal=284, total=951.
  - COMBINED_ESD_CREMA-D scanned (no-surprise): emergency=667, normal=284, total=951.
- Kept estimated rows unchanged and still explicitly marked as `count_source=estimated`.
- Kept default mainline policy as `surprise_excluded`; `surprise_included` remains sensitivity-only.
- ESD scanned rows remain zero because ESD audio is license-gated and not yet staged into `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd`.
