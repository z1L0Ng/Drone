# Phase2 Mapping Audit 2026W14

## Audit Basis
- Source of policy: `multilingual_mapping_contract_2026w14.md`
- Source of priority: `multilingual_priority_scorecard_2026w14.md`
- Mainline mapping contract: `surprise_excluded`

## Contract Checks
1. emergency labels must include `anger+fear` for strict comparability
2. normal labels must include `neutral` (`calm` optional)
3. `surprise` must stay out of mainline mapping
4. language must pass minimum sample gate (estimated now; scanned later)

## Per-Language Audit

### Italian (EMOZIONALMENTE) - Tier-1
- Mapping observed: `emergency=anger|fear`, `normal=neutral|calm`
- Semantic match level: `strict`
- Sample status:
  - estimated: `emergency≈1900-2100`, `normal≈900-1100` (pass)
  - scanned: pending
- Audit result: `GO (estimated track)`, `HOLD (scanned track pending)`
- Risks: acted speech domain shift; exact per-class counts pending local scan

### German (EMO-DB) - Tier-1
- Mapping observed: `emergency=anger|fear`, `normal=neutral`
- Semantic match level: `strict`
- Sample status:
  - estimated: `emergency≈150-220`, `normal≈60-90` (pass)
  - scanned: pending
- Audit result: `GO (estimated track)`, `HOLD (scanned track pending)`
- Risks: small corpus variance; acted speech domain shift

### French (CaFE) - Tier-2
- Mapping observed: `emergency=anger|fear`, `normal=neutral`
- Semantic match level: `strict`
- Sample status:
  - estimated: `emergency=288`, `normal=72` (pass)
  - scanned: pending
- Audit result: `GO (estimated track)`, `HOLD (scanned track pending)`
- Risks: CC BY-NC-SA non-commercial constraint

### Chinese (Mandarin, ESD ZH) - Reference
- Mapping observed: `emergency=anger`, `normal=neutral`
- Semantic match level: `partial` (fear missing)
- Sample status: large estimated pool, scanned pending
- Audit result: `HOLD` for strict comparable mainline; bridge-only candidate
- Risks: semantic gap vs English baseline; data license research-only

### Portuguese (Brazil, EmoUERJ) - Reference
- Mapping observed: `emergency=anger`, `normal=neutral`
- Semantic match level: `partial` (fear missing)
- Sample status: estimated pass, scanned pending
- Audit result: `HOLD` for strict comparable mainline; bridge-only candidate
- Risks: semantic gap vs English baseline

## Immediate Phase2 Recommendation
1. Keep immediate execution order: Italian -> German -> French.
2. For strict-comparable multilingual expansion, prioritize Italian + German once scanned counts are available.
3. If any Tier-1 scanned gate fails, replace with French (Tier-2 strict fallback).

## Pending Items Before Final Lock-In
- Populate scanned counts for Italian/German/French in phase2 manifest.
- Recompute scorecard ranking using scanned counts only.
- Confirm final top-2 strict languages and freeze phase2 language scope.
