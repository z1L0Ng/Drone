# Phase2 Multilingual Plan 2026W14

## Scope Guardrails
- Branch: `codex/acoustic-2026w14-phase1`
- Scope: acoustic/dataset analysis only
- No model architecture edits
- No training orchestration edits

## Inputs Used (Mandatory)
- `analysis/cross_language_emergency/multilingual_priority_scorecard_2026w14.md`
- `analysis/cross_language_emergency/multilingual_mapping_contract_2026w14.md`

## Objective
After the English gate pass in phase1, prepare multilingual expansion with explicit semantic comparability to English (`surprise_excluded` mainline).

## Canonical Mapping Baseline (must preserve)
- emergency = `anger + fear`
- normal = `neutral (+ calm if available)`
- `surprise` remains sensitivity-only appendix

## Execution Order
1. Tier-1 language A: Italian (EMOZIONALMENTE)
2. Tier-1 language B: German (EMO-DB)
3. Tier-2 fallback: French (CaFE)

## Go/Hold Rule Per Language
A language is `go` only if all are true:
1. `semantic_match_level = strict`
2. estimated usable samples pass threshold (`emergency>=120` and `normal>=60`)
3. license is open for academic use and source is reachable

Otherwise set `hold` and move to next priority language.

## First-Batch Deliverables (this run)
1. `phase2_multilingual_dataset_manifest_2026w14.csv`
   - separate `estimated` vs `scanned`
   - no fabricated scanned counts
2. `phase2_mapping_audit_2026w14.md`
   - per-language mapping contract compliance audit

## Current First-Batch Decision Snapshot
- Italian: `go` (strict mapping, estimated sample sufficient, open license)
- German: `go` (strict mapping, estimated sample sufficient, open license)
- French: `go` (strict mapping, estimated sample sufficient, academic-usable but NC risk)

## Scan-Return Update Trigger
When server-side multilingual audio scans become available:
1. fill `scanned` rows in phase2 manifest
2. re-run mapping audit gate using scanned counts
3. finalize first two expansion languages from strict pool by scorecard ranking

## Expected Next Decision (post-scan)
- Priority pick: Italian + German
- French stays immediate backup if any Tier-1 language fails scanned gate
