# 2026W14 跨语言 emergency 声学共性长周期分析报告（中文）

## 1. 数据与映射
- 主分析映射：`emergency=anger+fear`，`normal=neutral(+calm)`；`surprise`仅用于敏感性分析。
- 语种覆盖：中文、英文、法语、意大利语、波兰语（>=5 且覆盖中/英/法）。
- 数据与计数见：`dataset_registry_2026w14.csv`、`fig01_sample_coverage_by_language.png`。

## 2. 语言内差异（主分析）
- 每语言每特征的 Cohen's d 与 bootstrap 95%CI 见：`feature_effects_by_language_2026w14.csv`。
- 热力图见：`fig02_effectsize_heatmap_language_feature.png`。
- 频带/alpha/centroid-bandwidth/pitch-energy 见：fig04~fig07。

## 3. 跨语言共享特征判定
共享规则：方向一致率>=80%、|pooled effect|>=0.30、95%CI不跨0。
- 元分析与异质性见：`shared_features_meta_2026w14.csv`、`fig03_pooled_effect_forest_shared_features.png`。
- 共享特征 Top 列表：
  - pitch_mean: pooled=0.789, CI=[0.546,1.032], I²=95.4%
  - energy_env_std: pooled=0.552, CI=[0.265,0.838], I²=96.8%
  - pitch_energy_corr: pooled=0.539, CI=[0.340,0.737], I²=93.4%
  - spectral_bandwidth: pooled=0.477, CI=[0.342,0.611], I²=85.4%
  - spectral_rolloff: pooled=0.458, CI=[0.280,0.636], I²=91.8%
  - zcr: pooled=0.430, CI=[0.245,0.615], I²=92.4%
  - spectral_centroid: pooled=0.422, CI=[0.215,0.629], I²=94.0%
  - alpha_ratio: pooled=0.384, CI=[0.240,0.529], I²=87.5%
- 分歧特征见：`divergence_features_2026w14.csv`、`fig08_shared_vs_divergent_summary.png`。
  - 分歧: pitch_std, pooled=0.105, consistency=0.60, I²=98.6%
  - 分歧: pause_ratio, pooled=0.179, consistency=0.60, I²=98.2%
  - 分歧: harmonic_ratio, pooled=-0.017, consistency=0.60, I²=97.3%
  - 分歧: energy_env_slope, pooled=-0.055, consistency=0.60, I²=92.1%
  - 分歧: low_band_ratio, pooled=-0.287, consistency=0.80, I²=97.6%

## 4. 敏感性分析（含 surprise）
- 仅用于稳健性检查，不进入主结论。
- pooled effect 变化最大的特征：
  - pitch_std: main=0.105, sensitivity=0.210, delta=+0.106
  - alpha_ratio: main=0.384, sensitivity=0.302, delta=-0.082
  - high_band_ratio: main=0.365, sensitivity=0.293, delta=-0.071
  - harmonic_ratio: main=-0.017, sensitivity=-0.085, delta=-0.068
  - low_band_ratio: main=-0.287, sensitivity=-0.223, delta=+0.063

## 5. 结论（证据绑定）
1. 存在可迁移的跨语言共享声学特征（见 shared_features_meta + fig03）。
2. 高频能量、谱中心/带宽与 prosody（pitch-energy）在多数语言方向一致（见 fig04~fig07）。
3. 部分特征存在较高异质性，需在训练中降权一致性约束（见 divergence csv + fig08）。

## 6. 训练与预处理可执行建议
- 详见：`training_preprocessing_recommendations_2026w14.md`（参数化可直接执行）。
