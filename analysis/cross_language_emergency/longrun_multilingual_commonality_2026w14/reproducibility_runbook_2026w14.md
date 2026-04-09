# Reproducibility Runbook 2026W14

## Environment
```bash
cd /Users/zilongzeng/Research/Drone
python3 -m pip install datasets pyarrow librosa soundfile pandas matplotlib scipy
```

## Run Full Pipeline
```bash
cd /Users/zilongzeng/Research/Drone
python3 scripts/run_longrun_multilingual_commonality_2026w14.py \
  --output-root analysis/cross_language_emergency/longrun_multilingual_commonality_2026w14 \
  --bootstrap 700 \
  --seed 20260409
```

## Main Outputs
- dataset_registry_2026w14.csv
- mapping_contract_2026w14.md
- feature_effects_by_language_2026w14.csv
- shared_features_meta_2026w14.csv
- divergence_features_2026w14.csv
- training_preprocessing_recommendations_2026w14.md
- final_report_zh_2026w14.md
- final_report_en_2026w14.md
- figures/*.png

## Notes
- Mainline excludes `surprise`; sensitivity section includes it.
- Estimated counts are computed from raw label scan.
- Scanned counts are computed from successfully decoded + feature-extracted samples.
