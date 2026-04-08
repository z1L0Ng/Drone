# Phase2 Top2 Gloss Clusters 2026W14

## Scope
- Top2 lexical-first languages: Quechua + Polish.
- Canonical mapping fixed: emergency=anger+fear; normal=neutral(+calm); surprise sensitivity-only.

## Cluster Construction
1. Candidate lexical unit = `normalized_utterance_text`.
2. Keep only rows with `include_flag=1` and canonical labels in {emergency, normal}.
3. Cross-language strict gloss cluster requires non-NA `english_gloss` match; current batch has no open English gloss, so strict cross-language clusters = 0.

## Per-Language Top Lexical Units (frequency)

### Quechua
| normalized_utterance_text | freq |
|---|---:|
| llasa | 18 |
| kuchuna | 18 |
| chay ruwayta mana chaskisqachu millaypunin chayqa consejo viceministro nisqakunamanta hamuq. | 12 |
| tintinqa wasimasinchispa sach'akunapin wiñan | 12 |
| phiña | 12 |
| sasachaykuna | 12 |
| sapallanmi chay runaqa waqtuta ukyarapusqa | 12 |
| waqayuspan ripun | 12 |
| manan waylluytaqa huchapi t ́ikachinachu. | 12 |
| raphi | 12 |
| saqesqay hinallan kashan | 12 |
| ¿pitaq chay t’ikakunatari t ́iraran? | 12 |

### Polish
| normalized_utterance_text | freq |
|---|---:|
| nie waśńmy się ze sobą | 27 |
| moja ciocia jest bardzo pomocna | 27 |
| w parku rośnie ogromne drzewo | 27 |
| ten miesiąc minął bardzo szybko | 27 |
| dzieci muszą dużo jeść | 27 |
| przestań go judzić | 27 |
| aby upiec ciasto muszę kupić mączkę | 26 |
| egipcjanie uważali ibisy za święte | 26 |
| człowiek zaczyna umierać już w momencie narodzin | 26 |
| ten pomysł trąci brakiem realizmu | 26 |
| żołwica to dawne określenie na siostrę męża | 26 |
| lubię czytać przed snem | 26 |

## Cross-Language Gloss Status
- Strict comparable gloss clusters: **0** (english_gloss unavailable for both top2 datasets).
- Action to unlock strict clustering: add human-curated or officially provided English gloss table keyed by `sample_id` or sentence id.
