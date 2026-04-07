# Meeting Evidence Table 2026W14 (Phase1 CREMA-D)

- Main mapping: `surprise_excluded` (emergency=anger+fear; normal=neutral[+calm if present]).
- Statistics source: `findings_phase1_cremad.md` (refreshed run, no training).

| feature | emergency_mean | normal_mean | direction | delta(em-normal) | cohen_d | effect_magnitude | stat_summary | risk_note |
|---|---:|---:|---|---:|---:|---|---|---|
| alpha_ratio | 0.2452 | 0.0907 | emergency_higher | 0.1545 | 0.4444 | small | delta=0.1545; cohen_d=0.4444 (small) | Acted speech + clean recording; potential domain shift to real emergency audio. |
| spectral_centroid_hz | 612.0382 | 484.4983 | emergency_higher | 127.5399 | 0.4874 | small | delta=127.5399; cohen_d=0.4874 (small) | Acted speech + clean recording; potential domain shift to real emergency audio. |
| spectral_bandwidth_hz | 607.1720 | 535.9418 | emergency_higher | 71.2302 | 0.4365 | small | delta=71.2302; cohen_d=0.4365 (small) | Acted speech + clean recording; potential domain shift to real emergency audio. |
| energy_low_prop | 0.4491 | 0.5613 | emergency_lower | -0.1122 | -0.5023 | medium | delta=-0.1122; cohen_d=-0.5023 (medium) | Acted speech + clean recording; potential domain shift to real emergency audio. |
| energy_mid_prop | 0.4977 | 0.4085 | emergency_higher | 0.0892 | 0.4178 | small | delta=0.0892; cohen_d=0.4178 (small) | Acted speech + clean recording; potential domain shift to real emergency audio. |
| energy_high_prop | 0.0531 | 0.0301 | emergency_higher | 0.0230 | 0.3928 | small | delta=0.0230; cohen_d=0.3928 (small) | Acted speech + clean recording; potential domain shift to real emergency audio. |
