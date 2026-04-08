# Phase2 Lexical Unblock Top2 2026W14

## Ranking Rule
Priority score order:
1. lexical readiness
2. semantic strictness
3. sample size
4. license risk

## Top-2 Actionable Languages
1. **Quechua (`quechua`)**
   - Why: lexical readiness `ready` (verbatim transcription + translation), semantic `strict`, largest available pool (`files=12416`), license CC-BY-4.0.
   - Status: `go`
2. **Polish (`nemo`)**
   - Why: lexical readiness `ready` (raw_text + normalized_text), semantic `strict`, substantial pool (`files=4481`).
   - Status: `go`

## Fallback (1)
- **Italian (`emozionalmente`)**
  - Why fallback: semantic `strict` and large estimated usable sample, but lexical mode is template-id (`s0..`) so it is `partial` readiness until sentence-id mapping is staged.

## Notes
- This lexical-first top2 differs from earlier mapping-first tiering by prioritizing immediate transcript usability.
- Canonical mapping remains unchanged: emergency=anger+fear, normal=neutral(+calm), surprise sensitivity-only.
