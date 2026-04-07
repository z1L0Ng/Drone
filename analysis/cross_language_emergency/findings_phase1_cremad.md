# Findings Phase1 (CREMA-D, Main Mapping: surprise_excluded)

- Generated at: 2026-04-07T12:17:47
- Mapping: emergency=anger+fear; normal=neutral (+ calm if present)
- Sample counts: emergency=2071, normal=884, total=2955
- Code counts used: ANG=1035, FEA=1036, NEU=884, CAL=0

## Metric Summary

| metric | emergency_mean | normal_mean | delta(em-normal) | cohen_d |
|---|---:|---:|---:|---:|
| alpha_ratio | 0.2405 | 0.0834 | 0.1571 | 0.4506 |
| spectral_centroid_hz | 589.9442 | 466.7954 | 123.1487 | 0.5198 |
| spectral_bandwidth_hz | 594.3455 | 524.0801 | 70.2654 | 0.4497 |
| energy_low_prop | 0.4417 | 0.5567 | -0.1150 | -0.5165 |
| energy_mid_prop | 0.5110 | 0.4177 | 0.0933 | 0.4421 |
| energy_high_prop | 0.0473 | 0.0256 | 0.0216 | 0.4318 |

## Main Takeaways

- Compare four figures jointly; no single acoustic feature should be over-interpreted.
- This is evidence for class-level acoustic separability, not full model performance.
