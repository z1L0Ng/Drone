# Training & Preprocessing Recommendations 2026W14

## Evidence Index
- Coverage imbalance: `dataset_registry_2026w14.csv`, `fig01_sample_coverage_by_language.png`
- Language-feature effects: `feature_effects_by_language_2026w14.csv`, `fig02_effectsize_heatmap_language_feature.png`
- Shared features and heterogeneity: `shared_features_meta_2026w14.csv`, `fig03_pooled_effect_forest_shared_features.png`, `fig08_shared_vs_divergent_summary.png`
- Frequency/pitch-prosody evidence: `fig04_frequency_band_energy_comparison.png`, `fig05_alpha_ratio_multilingual.png`, `fig06_centroid_bandwidth_multilingual.png`, `fig07_pitch_energy_envelope_multilingual.png`

## Training-Side (Executable)
1. Class-language reweighting sampler
   - Use per-language-class sampling weight: `w(l,c)=clip(1/sqrt(n_scanned(l,c)), 0.5, 2.5)`.
   - Apply at dataloader level for emergency/normal pairs to reduce French/Chinese normal under-sampling risk (see fig01).
2. Shared-feature auxiliary loss (multitask)
   - Add regression head on shared features: `pitch_mean, energy_env_std, pitch_energy_corr, spectral_bandwidth, spectral_rolloff, zcr`.
   - Loss: `L = L_cls + 0.20 * L_shared` (MSE on z-normalized targets computed from preprocessing cache).
3. Heterogeneity-aware training schedule
   - For high-I² features (see divergence csv), reduce cross-language consistency penalty on those channels.
   - Suggested: `lambda_consistency = 0.12` for shared features, `0.04` for divergent set.
4. Emergency-margin stabilization
   - Use focal loss on emergency class: `gamma=1.5`, `alpha_emergency=1.25`, `alpha_normal=1.0`.
   - Tie margin schedule to shared-feature confidence: increase margin by `+0.05` when batch shared-feature score passes threshold.

## Preprocessing-Side (Executable)
1. Loudness and dynamic normalization
   - Peak normalize to `-1 dBFS`, then RMS target to `-23 LUFS` equivalent level by gain normalization.
   - Reason: reduces cross-language envelope scale drift (fig07).
2. Frequency emphasis guided by shared effects
   - Apply mild high-band emphasis for 2-6 kHz: `+2 dB` shelving before feature extraction.
   - Keep low-band denoise at 0-80 Hz high-pass to remove hum; supported by band-energy differences (fig04).
3. Prosody-preserving augmentation constraints
   - Time-stretch range `0.95-1.05`, pitch-shift `±1 semitone`, SNR noise mix `15-25 dB`.
   - Avoid aggressive augmentation that distorts pitch-energy envelope cues (fig07).
4. Feature cache for training reuse
   - Cache shared and divergent feature vectors per sample to `parquet`; use in sampler and auxiliary loss without recomputing STFT.
