# Phase2 Top2 Gloss Quality Audit 2026W14

## Coverage by Language
| language | rows_total | with_source_text | gloss_filled | gloss_na | conf_medium | conf_low | strict_eligible_rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| Quechua | 12416 | 12416 | 2231 | 10185 | 2231 | 10185 | 2231 |
| Polish | 4481 | 4481 | 4481 | 0 | 4481 | 0 | 4481 |

## Gloss Source Registry
| gloss_source | rows |
|---|---:|
| quechua.misc_sentence.translation.spa + googletranslate(es->en) | 12416 |
| nemo.misc_sentence.raw_text + googletranslate(pl->en) | 4481 |

## Compliance
1. every gloss row has gloss_source: PASS
2. low-confidence rows excluded from strict cluster claims: PASS
3. strict cluster summary includes clusters / covered / left(NA+partial): PASS

## Residual Risks
- Machine translation quality varies; publication-grade use should include human verification on sampled rows.
- Priority-batch translation leaves some Quechua rows as NA by design.
