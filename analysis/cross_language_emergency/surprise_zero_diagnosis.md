# Surprise Zero Diagnosis (Phase1 CREMA-D)

## Question
Why is `surprise` count equal to 0 in phase1 outputs?

## Diagnosis Result
- Root cause (primary): dataset payload does not contain a surprise emotion code in filenames.
- Root cause (secondary): current mapping/scan flow does not introduce surprise from any fallback label source.
- Parser-risk note: analyzer code currently whitelists CREMA emotion codes without `SUR`; if `SUR` appears in future payloads, it would be dropped unless whitelist is extended.

## Evidence
- Raw scan path: `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/crema_d`
- Raw wav count: `6966`
- Emotion code counts parsed from filename token 3:
  - `DIS=1191`
  - `SAD=1190`
  - `HAP=1190`
  - `ANG=1190`
  - `FEA=1189`
  - `NEU=1016`
  - `SUR=0`
- Additional grep check on filenames: `_SUR_` matches `0` files.

## Conclusion
`surprise=0` is data-availability driven for the current CREMA-D payload, not a meeting-blocking bug in the phase1 result interpretation.

## Minimal Fix Suggestion
1. Keep phase1 main conclusion unchanged (`surprise_excluded` remains default).
2. Add `SUR` to code whitelist and log unknown emotion-code counts during scan for forward compatibility.
3. In reports, annotate sensitivity branch as: "no effective sample change when SUR is absent in payload".
