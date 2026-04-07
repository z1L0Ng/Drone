# Findings Phase1 (CREMA-D, Main Mapping: surprise_excluded)

- Generated at: 2026-04-07T13:48:48
- Mapping: emergency=anger+fear; normal=neutral (+ calm if present)
- Sample counts: emergency=2539, normal=1086, total=3625
- Code counts used: ANG=1270, FEA=1269, NEU=1086, CAL=0

## Metric Summary

| metric | emergency_mean | normal_mean | delta(em-normal) | cohen_d |
|---|---:|---:|---:|---:|
| alpha_ratio | 0.2452 | 0.0907 | 0.1545 | 0.4444 |
| spectral_centroid_hz | 612.0382 | 484.4983 | 127.5399 | 0.4874 |
| spectral_bandwidth_hz | 607.1720 | 535.9418 | 71.2302 | 0.4365 |
| energy_low_prop | 0.4491 | 0.5613 | -0.1122 | -0.5023 |
| energy_mid_prop | 0.4977 | 0.4085 | 0.0892 | 0.4178 |
| energy_high_prop | 0.0531 | 0.0301 | 0.0230 | 0.3928 |

## Main Takeaways

- Compare four figures jointly; no single acoustic feature should be over-interpreted.
- This is evidence for class-level acoustic separability, not full model performance.
