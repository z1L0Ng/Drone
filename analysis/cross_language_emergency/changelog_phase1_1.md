# Changelog Phase 1.1

- Fixed ESD label mapping: removed `fear` from ESD emergency labels where ESD has zero fear samples.
- Added real scan count stream in `sample_count_table_2026w14.csv` with `count_source=scanned` and scan diagnostics (`audio_files_scanned`, `label_detected_files`, `unmapped_files`).
- Kept estimated counts in parallel with explicit `count_source=estimated` and `count_type=estimated`.
- Updated `dataset_options_2026w14.md` to set default mainline as `surprise_excluded`; `surprise_included` is now sensitivity appendix only.
- Updated risk notes to reflect scan-empty condition until isolated download root is populated.
