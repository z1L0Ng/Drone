# Multilingual Mapping Contract 2026W14

## Goal
确保多语言扩展与英语 phase1 主分析严格可比，避免“标签语义漂移”导致的伪差异。

## Canonical Label Space (固定)
- 主口径（默认）：`surprise_excluded`
  - `emergency = anger + fear`
  - `normal = neutral (+ calm if available)`
- 敏感性附录：`surprise_included`
  - `emergency = anger + fear + surprise`
  - `normal = neutral (+ calm if available)`

## Dataset-to-Canonical Mapping
| dataset | language | raw labels used for emergency | raw labels used for normal | strict comparable with English? |
|---|---|---|---|---|
| CREMA-D | English | anger, fear | neutral | yes |
| EMOZIONALMENTE | Italian | anger, fear | neutral (and calm if present) | yes |
| EMO-DB | German | anger, fear | neutral | yes |
| CaFE | French | anger, fear | neutral | yes |
| ESD (ZH) | Chinese | anger | neutral | no (fear missing) |
| EmoUERJ | Portuguese | anger | neutral | no (fear missing) |

## Inclusion / Exclusion Rules (必须执行)
1. 仅纳入可映射到 canonical label 的样本。
2. `happy/sad/disgust/boredom/other` 在主分析中一律排除。
3. `surprise` 默认不纳入主分析，只能出现在敏感性附录。
4. 缺 `fear` 的数据集不得进入“严格可比主结论”，只能作为 bridge 分析。
5. 每个数据集都必须输出 `included / excluded / unmapped` 计数。

## Comparability Gate (进入跨语言主结论前)
1. 口径一致：必须满足 `surprise_excluded` 主映射。
2. 样本下限（scanned）：`emergency>=120` 且 `normal>=60`。
3. 类别平衡：`0.33 <= emergency/normal <= 3.0`；超出则标记 imbalance 风险。
4. 特征流程一致：沿用英语 phase1 同一套特征与统计摘要格式。

## Output Contract (服务器结果回来后必须同步刷新)
- `analysis/cross_language_emergency/sample_count_table_2026w14.csv`
- `analysis/cross_language_emergency/meeting_evidence_table_2026w14.md`
- `analysis/cross_language_emergency/meeting_evidence_table_2026w14.csv`
- `analysis/cross_language_emergency/onepager_2026w14_phase1.md`
- `analysis/cross_language_emergency/multilingual_priority_scorecard_2026w14.md`

## Decision Contract
- 默认从“strict comparable pool”选前 2 语言进入下一轮。
- 若只够 1 个 strict 语言，第二个名额可从 bridge 语言补位，但必须在 meeting 结论中单独标注“语义非严格同口径”。
