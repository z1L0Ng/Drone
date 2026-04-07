# ESD Rescan Instructions (One-pass Update)

## Preconditions
- ESD audio has been staged at:
  - `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd`
- Current branch: `codex/acoustic-2026w14-phase1`

## One-pass Update Command
Run from repo root:

```bash
python3 scripts/build_dataset_manifest_2026w14.py \
  --output-dir analysis/cross_language_emergency \
  --phase phase1_en \
  --download-root /tmp/drone_acoustic_2026w14_phase1_downloads \
  --datasets esd,crema_d \
&& python3 scripts/render_dataset_options_2026w14.py \
  --input-dir analysis/cross_language_emergency \
  --output-md analysis/cross_language_emergency/dataset_options_2026w14.md
```

## Optional Refresh Of CREMA-D Acoustic Evidence
(Use only if you also want regenerated plots/findings):

```bash
python3 scripts/analyze_phase1_cremad_acoustics.py \
  --input-root /tmp/drone_acoustic_2026w14_phase1_downloads/raw/crema_d \
  --output-root analysis/cross_language_emergency
```

## Verify Rescan Success
- Check ESD scanned rows become non-zero:

```bash
rg -n "^phase1_en,ESD,scanned" analysis/cross_language_emergency/sample_count_table_2026w14.csv
```

- Confirm default policy still intact:

```bash
rg -n "surprise_excluded" analysis/cross_language_emergency/dataset_options_2026w14.md
```
