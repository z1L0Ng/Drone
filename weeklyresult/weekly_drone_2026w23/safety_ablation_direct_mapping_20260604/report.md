# Safety-State Abstraction Ablations

This is an offline/action-simulation analysis. It does not run a drone, validate flight safety, train models, or modify the paper.

## Direct Mapping Summary

| Source | n | Action pressure / 100 windows | Unknown false action rate | Missed emergency action rate | Unauthorized movement actions |
|---|---:|---:|---:|---:|---:|
| akouo_reference_snr_m10db | 10008 | 67.5659 | 0.1634 | 0.1469 | 3203 |
| asr_whisper_tiny_parser_snr_m10db | 10008 | 12.2502 | 0.0204 | 0.7791 | 421 |
| embedded_user_study_v4_candidate | 1462 | 68.8098 | 0.1625 | 0.3782 | 634 |

## No-Unknown Ablation Summary

| Source | Method | True unknown forced action rate | Additional action pressure / 100 windows | Caveat |
|---|---|---:|---:|---|
| akouo_reference_snr_m10db | label_only_bounds | 1.0000 | 32.4341 | Only labels/confusion are available. Total true-unknown forced-action rate is exact under a no-unknown classifier, but emergency-vs-movement split is bounded rather than measured. |
| asr_whisper_tiny_parser_snr_m10db | label_only_bounds | 1.0000 | 87.7498 | Only labels/confusion are available. Total true-unknown forced-action rate is exact under a no-unknown classifier, but emergency-vs-movement split is bounded rather than measured. |
| embedded_user_study_v4_candidate | exact_probability_argmax_between_emergency_and_movement | 1.0000 | 31.1902 | Exact for this source because per-class probabilities are available. |

## Paper Boundary

Paper-usable as evidence that direct label-to-action mapping creates action pressure and that the unknown/fallback state is a containment mechanism. Do not describe these numbers as flight validation or as measured UAV actuation.

## Result Tree

See `result_tree.txt`.
