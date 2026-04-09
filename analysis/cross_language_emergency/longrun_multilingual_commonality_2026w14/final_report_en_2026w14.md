# 2026W14 Long-Run Multilingual Emergency Acoustic Commonality Report (EN)

## 1. Data and Mapping
- Mainline mapping: `emergency=anger+fear`, `normal=neutral(+calm)`; `surprise` is sensitivity-only.
- Language coverage: Chinese, English, French, Italian, Polish.
- Dataset and counts: `dataset_registry_2026w14.csv`, `fig01_sample_coverage_by_language.png`.

## 2. Within-Language Effects
- Per-language Cohen's d and bootstrap 95%CI: `feature_effects_by_language_2026w14.csv`.
- Heatmap: `fig02_effectsize_heatmap_language_feature.png`.
- Frequency/alpha/centroid-bandwidth/pitch-energy evidence: fig04~fig07.

## 3. Cross-Language Shared Features
Shared rule: direction consistency >= 80%, |pooled effect| >= 0.30, and 95% CI excluding 0.
- Meta-analysis + heterogeneity: `shared_features_meta_2026w14.csv`, `fig03_pooled_effect_forest_shared_features.png`.
- Shared: pitch_mean (pooled=0.789, CI=[0.546,1.032], I²=95.4%)
- Shared: energy_env_std (pooled=0.552, CI=[0.265,0.838], I²=96.8%)
- Shared: pitch_energy_corr (pooled=0.539, CI=[0.340,0.737], I²=93.4%)
- Shared: spectral_bandwidth (pooled=0.477, CI=[0.342,0.611], I²=85.4%)
- Shared: spectral_rolloff (pooled=0.458, CI=[0.280,0.636], I²=91.8%)
- Shared: zcr (pooled=0.430, CI=[0.245,0.615], I²=92.4%)
- Shared: spectral_centroid (pooled=0.422, CI=[0.215,0.629], I²=94.0%)
- Shared: alpha_ratio (pooled=0.384, CI=[0.240,0.529], I²=87.5%)
- Divergent features: `divergence_features_2026w14.csv`, `fig08_shared_vs_divergent_summary.png`.
- Divergent: pitch_std (pooled=0.105, consistency=0.60, I²=98.6%)
- Divergent: pause_ratio (pooled=0.179, consistency=0.60, I²=98.2%)
- Divergent: harmonic_ratio (pooled=-0.017, consistency=0.60, I²=97.3%)
- Divergent: energy_env_slope (pooled=-0.055, consistency=0.60, I²=92.1%)
- Divergent: low_band_ratio (pooled=-0.287, consistency=0.80, I²=97.6%)

## 4. Sensitivity (with surprise)
- Sensitivity is reported separately and does not alter mainline mapping claims.
- pitch_std: main=0.105, sensitivity=0.210, delta=+0.106
- alpha_ratio: main=0.384, sensitivity=0.302, delta=-0.082
- high_band_ratio: main=0.365, sensitivity=0.293, delta=-0.071
- harmonic_ratio: main=-0.017, sensitivity=-0.085, delta=-0.068
- low_band_ratio: main=-0.287, sensitivity=-0.223, delta=+0.063

## 5. Actionable Conclusion
1. Stable transferable acoustic cues exist across languages under the defined rule.
2. Shared cues are strongest in spectral-energy and prosody-linked descriptors.
3. Divergent cues require heterogeneity-aware weighting in training.
4. Execution-grade training/preprocessing parameters are provided in `training_preprocessing_recommendations_2026w14.md`.
