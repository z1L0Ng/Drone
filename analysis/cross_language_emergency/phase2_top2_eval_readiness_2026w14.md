# Phase2 Top2 Eval Readiness 2026W14

## Strict Cluster Status
- strict_cluster_count: **8**
- benchmark_usable_rows_total: **7805**

## Benchmark Usable Rows by Language and Canonical Label
| language | emergency | normal | total |
|---|---:|---:|---:|
| Quechua | 2753 | 2758 | 5511 |
| Polish | 1485 | 809 | 2294 |

## Benchmark Usable Rows by Language and Split
| language | train | dev | test | total |
|---|---:|---:|---:|---:|
| Quechua | 1654 | 182 | 3675 | 5511 |
| Polish | 1833 | 239 | 222 | 2294 |

## Exclusion Summary (use_for_eval=0)
| exclusion_reason | rows |
|---|---:|
| non_canonical_label | 9092 |

## Remaining Blockers for Local Real-World Gate Integration
- Gloss quality is MT-derived; no human validation subset is attached yet.
- Concept IDs are gloss-string based; synonym collapse across languages is not yet audited manually.
- Domain shift remains (acted speech vs in-the-wild emergency speech).
