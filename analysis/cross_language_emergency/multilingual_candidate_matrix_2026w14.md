# Multilingual Candidate Matrix 2026W14

## Gate 前提
- English gate（CREMA-D, `surprise_excluded`）结果：`PASS`。
- 扩展口径保持与英语主分析一致：`emergency = anger + fear`，`normal = neutral (+ calm if available)`。

## 候选矩阵（按优先级）
| priority | language | dataset | official link | license / academic use | estimated usable samples (surprise_excluded) | emergency/normal 映射可行性 | 主要风险 |
|---|---|---|---|---|---:|---|---|
| P1 | Italian | EMOZIONALMENTE | https://audeering.github.io/datasets/datasets/emozionalmente.html | CC BY 4.0, unrestricted (可学术/商用，需署名) | emergency≈1900-2100, normal≈900-1100（基于 total=6902 的类别近似估计，待扫描校正） | 高：标签含 anger/fear/neutral，可与英语同口径直接对照 | 类别分布官方页未给精确每类计数，需下载后实扫；演员语音域偏移 |
| P1 | German | EMO-DB | https://audeering.github.io/datasets/datasets/emodb.html | CC0-1.0, unrestricted (可学术/商用) | emergency≈150-220, normal≈60-90（total=535，估计区间） | 高：标签含 anger/fear/neutral，语义同构 | 样本总体较小，方差较大；演员录音室语音 |
| P2 | French | CaFE | https://doi.org/10.5281/zenodo.1219621 | CC BY-NC-SA 4.0（学术可用，非商用） | emergency=288, normal=72（由数据设计可推导） | 高：标签含 anger/fear/neutral（另有 surprise 仅作敏感性） | 非商用限制；样本偏小；演员语音 |
| P2 | Chinese (Mandarin) | ESD (ZH split) | https://github.com/HLTSingapore/Emotional-Speech-Data | 仓库 MIT，但数据使用条款为 research-only（需签许可） | emergency=3500, normal=3500（按每语言 350 utterances x 10 speakers x 每情绪 1 类推导） | 中：缺 fear，主口径只能用 anger vs neutral；与英语(anger+fear)存在语义缺口 | 许可口径存在“代码 MIT / 数据 research-only”双轨；需严格记录映射差异 |
| P3 | Portuguese (Brazil) | EmoUERJ | https://audeering.github.io/datasets/datasets/emouerj.html | ODbL-1.0, unrestricted（可学术/商用，需满足 ODbL 条款） | emergency≈150-250, normal≈150-250（total=780，标签含 anger/neutral，不含 fear） | 中-低：仅 anger 可入 emergency，缺 fear | 语义对照不完整；样本中等；演员语音 |

## 建议进入下一轮的语言
1. Italian（样本与许可最稳，且可完整复用英语映射）。
2. German（同口径语义最干净，适合做“跨语言一致性”验证）。
3. French（可做补充验证；若需商用路线则降级）。

## 说明
- 上表为 phase1 后的候选扩展清单，不包含新增训练。
- 统一策略：先做下载后实扫计数，再决定是否进入同特征对比图（alpha ratio / spectral centroid-bandwidth / energy / pitch-energy envelope）。
- Japanese 公开许可且可稳定复用同口径映射的数据源在当前轮未锁定，建议单列待补项而非并入本轮优先集合。

## Source Notes
- ESD 官方 README 提供语言与样本结构，并注明“research purpose only”。
- CREMA-D/EMO-DB/EMOZIONALMENTE/EmoUERJ 的许可证、语言、文件规模来自 audEERING datasets 官方页面。
- CaFE 许可与数据结构来自 Zenodo/OpenAIRE 页面（CC BY-NC-SA、12 actors、6 emotions + neutral、双强度）。
