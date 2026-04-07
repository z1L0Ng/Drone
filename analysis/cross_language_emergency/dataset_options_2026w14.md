# Dataset Options 2026W14 (Phase1 English, Revision 1.1)

## 0) Default Analysis Policy

- Default main analysis mapping: `surprise_excluded`.
- Surprise handling: `surprise_included` is used only in sensitivity appendix.
- Reported counts include both `estimated` and `scanned` sources.

## 1) Candidate Dataset Table

| dataset | license | emergency_mapping(default) | normal_mapping(default) | est_default_em | est_default_normal | key_risks |
|---|---|---|---|---:|---:|---|
| ESD | Research-use license form (NUS/SUTD ESD agreement) | anger | neutral | 3500 | 3500 | license_restriction; label_mapping_gap(no_fear); acted_speech_domain_shift |
| CREMA-D | ODbL v1.0 | anger|fear | neutral | 2480 | 1240 | acted_speech_domain_shift; per_emotion_count_unknown_without_local_scan |

## 2) Top 3 Recommended Plans

| plan | reason | default(no-surprise, estimated em/normal/total) | sensitivity(with-surprise, estimated em/normal/total) | scanned(no-surprise em/normal/total) | effort | meeting_deliverability |
|---|---|---|---|---|---|---|
| Plan A: ESD + CREMA-D | Best English coverage and best resilience if one source is delayed. | 5980/4740/10720 | 9480/4740/14220 | 2539/1086/3625 | medium | high |
| Plan B: ESD only | Largest single-source sample pool; simplest preprocessing path. | 3500/3500/7000 | 7000/3500/10500 | 0/0/0 | low | high |
| Plan C: CREMA-D only | Commercial-friendly baseline but smaller speaker/style diversity. | 2480/1240/3720 | 2480/1240/3720 | 2539/1086/3625 | low | medium |

## 3) Single Recommendation

- Recommended: **Plan A: ESD + CREMA-D**.
- Use `surprise_excluded` as mainline and treat `surprise_included` as appendix sensitivity check.

## 4) Missing Information That Can Change Selection

- Exact ESD and CREMA-D counts after copying downloaded audio into isolated root.
- Whether deployment target requires strictly commercial-compatible datasets.

## 5) Risks And Limitations

- See: `risk_and_limitations_2026w14.md` (speaker, license, domain shift).
