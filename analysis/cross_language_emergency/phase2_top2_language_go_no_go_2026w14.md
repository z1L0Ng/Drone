# Phase2 Top2 Language Go/No-Go 2026W14

## Decision Table
| language | decision | usable_rows | emergency | normal | train | dev | test | rationale |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Quechua | go | 5511 | 2753 | 2758 | 1654 | 182 | 3675 | strict clusters available; both labels and train/test coverage present |
| Polish | go | 2294 | 1485 | 809 | 1833 | 239 | 222 | strict clusters available; both labels and train/test coverage present |

## Global Risks
- MT-derived glosses can introduce lexical noise; sample-level human check is still needed before external reporting.
- Acted dataset style may overstate separability relative to real emergency speech.
- License and redistribution constraints should be rechecked before packaging audio subsets.
