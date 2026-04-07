# Onepager 2026W14 Phase1 (Meeting-ready)

## 结论（3）
1. English gate: `PASS`（`surprise_excluded` 主口径下 emergency/normal 差异稳定）。
2. 主分析样本：emergency=2539, normal=1086，可直接用于会前简报。
3. 现阶段以英语证据为主；多语言扩展建议采用同口径语义映射（anger+fear vs neutral）。

## 证据（3）
1. Alpha ratio 差异：delta=0.1545。
2. Spectral centroid 差异：delta=127.54 Hz。
3. 6 个核心特征中，|Cohen's d|>=0.35 的特征数：6/6。

## 风险（2）
1. Acted speech 与真实紧急语音存在域偏移风险。
2. 当前 ESD 扫描数仍为 0，跨语言证据尚未实扫闭环。

## 下一步（2）
1. 触发条件：当 `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd` 可扫描音频>0 时，立即重扫并刷新计数与对比表。
2. 扩展优先级建议：先 Italian/German（含 anger+fear+neutral），再 Chinese（目前多依赖 anger vs neutral）。
