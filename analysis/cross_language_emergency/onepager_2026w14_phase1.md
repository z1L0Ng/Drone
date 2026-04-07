# Onepager 2026W14 Phase1 (Meeting-ready)

## 结论（3）
1. 在 `surprise_excluded` 主口径下，CREMA-D 显示 emergency 与 normal 存在稳定声学差异。
2. 差异主要体现在 alpha ratio、spectral centroid/bandwidth、以及中高频能量占比。
3. 当前结果可直接进入周四会前简报作为 phase1 证据。

## 证据（3）
1. 样本规模：main 映射 `emergency=2071`, `normal=884`（见 `findings_phase1_cremad.md`）。
2. effect size：关键特征 Cohen's d 约 0.43~0.52（small-to-medium）。
3. 图证完整：4 张核心图已产出（alpha ratio / spectral centroid-bandwidth / energy distribution / pitch-energy envelope）。

## 风险（2）
1. CREMA-D 为 acted speech，存在到真实紧急语音场景的域偏移风险。
2. 当前仅英语证据，跨语言结论需等待 ESD 补扫后再确认。

## 下一步（2）
1. 触发条件：当 `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd` 中可扫描音频>0 时，立刻执行一次 manifest/rescan 更新。
2. 完成 ESD 补扫后，复用同一证据表模板补中英对比，进入跨语言 phase2。
