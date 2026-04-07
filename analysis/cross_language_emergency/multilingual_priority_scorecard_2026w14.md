# Multilingual Priority Scorecard 2026W14

## Purpose
在服务器补扫结果返回后，使用统一评分规则，直接选出优先扩展的前 2 种语言，并保持与英语主口径可比。

## Hard Filters (必须先通过)
1. 开源可学术使用（license clear）。
2. 可形成 `emergency/normal` 二分类映射。
3. 至少满足一套可复现实扫计数（`scanned`）。

## Scoring Formula (100分)
`final_score = 40*Mapping + 30*Sample + 15*License + 10*Ops + 5*Risk`

各项取值范围 `0~1`：
- `Mapping`：与英语主口径一致度。
  - 1.0: 同时包含 `anger + fear + neutral(+calm)`
  - 0.6: 仅 `anger + neutral`（缺 fear）
  - 0.0: 无法稳定映射
- `Sample`：基于 `scanned(no-surprise)` 的可用样本。
  - 1.0: `emergency>=1000` 且 `normal>=500`
  - 0.7: `emergency>=300` 且 `normal>=150`
  - 0.4: `emergency>=120` 且 `normal>=60`
  - 0.0: 低于阈值
- `License`：许可可用性。
  - 1.0: unrestricted/CC0/CC-BY/ODbL(clear)
  - 0.6: research-only 或 NC
  - 0.0: 不明确或不可用
- `Ops`：接入与复扫难度。
  - 1.0: 路径/标签规则稳定、无需额外申请
  - 0.6: 需手工许可或额外转换
  - 0.3: 接入不稳定
- `Risk`：域偏移与标签噪声可控性。
  - 1.0: 风险较低
  - 0.6: 中等风险
  - 0.3: 高风险

## Provisional Ranking (当前预评分，待 scanned 校正)
| language | dataset | Mapping | Sample(est) | License | Ops | Risk | provisional_score | note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Italian | EMOZIONALMENTE | 1.0 | 0.9 | 1.0 | 0.8 | 0.6 | 91.0 | 口径最完整，样本预估充足 |
| German | EMO-DB | 1.0 | 0.4 | 1.0 | 0.9 | 0.6 | 76.0 | 语义同构强，但样本较小 |
| French | CaFE | 1.0 | 0.4 | 0.6 | 0.7 | 0.6 | 67.0 | 可做补充，但 NC 限制 |
| Chinese (Mandarin) | ESD(ZH) | 0.6 | 1.0 | 0.6 | 0.6 | 0.6 | 68.0 | 高样本但缺 fear，严格可比性不足 |
| Portuguese (Brazil) | EmoUERJ | 0.6 | 0.4 | 1.0 | 0.8 | 0.6 | 64.0 | anger-only emergency，语义缺口 |

## Decision Rule After Server Results
1. 先用 `scanned(no-surprise)` 更新每个语言的 `Sample` 分数。
2. 仅 `Mapping=1.0` 的语言进入“严格可比池”。
3. 在严格可比池中按 `final_score` 选前 2 名。
4. 若严格可比池不足 2 个，再从 `Mapping=0.6` 中补 1 个作为 bridge 语言，并在结论中标注“非严格同口径”。

## Current Recommended Top-2 (pre-scan)
1. Italian (EMOZIONALMENTE)
2. German (EMO-DB)

## Immediate Backup
- French (CaFE)：当需要第三语言补充且接受 NC 限制时启用。
