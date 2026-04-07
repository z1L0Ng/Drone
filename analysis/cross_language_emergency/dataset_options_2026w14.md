# Dataset Options 2026W14 (Phase1 English)

## 1) Candidate Dataset Table

| dataset | official_url | license | academic_usable | commercial_usable | languages | emergency_mapping | normal_mapping | est_emergency | est_normal | sampling_rate | duration_sec | key_risks |
|---|---|---|---|---|---|---|---|---:|---:|---|---|---|
| ESD | https://github.com/HLTSingapore/Emotional-Speech-Data | Research-use license form (NUS/SUTD ESD agreement) | yes | no | english,mandarin | anger|fear|surprise | neutral|calm | 7000 | 3500 | unknown_public_page | unknown_public_page | license_restriction; label_mapping_gap(no_fear); acted_speech_domain_shift |
| CREMA-D | https://audeering.github.io/datasets/datasets/crema-d.html | ODbL v1.0 | yes | yes | english | anger|fear|surprise | neutral|calm | 2480 | 1240 | 16000 | 1.3-5.0 | acted_speech_domain_shift; per_emotion_count_unknown_without_local_scan |

## 2) Top 3 Recommended Plans

| plan | reason | surprise_included (em/normal/total) | surprise_excluded (em/normal/total) | effort | meeting_deliverability |
|---|---|---|---|---|---|
| Plan A: ESD + CREMA-D | Best English coverage with complementary licensing profile. | 9480/4740/14220 | 5980/4740/10720 | medium | high |
| Plan B: ESD only | Largest single-source sample pool with direct emotional labels. | 7000/3500/10500 | 3500/3500/7000 | low | high |
| Plan C: CREMA-D only | Commercial-friendly baseline with clean and simple structure. | 2480/1240/3720 | 2480/1240/3720 | low | medium |

## 3) Single Recommendation

- Recommended: **Plan A: ESD + CREMA-D**.
- Why: highest usable English sample count for emergency/normal while preserving a commercial-usable anchor dataset.

## 4) Missing Information That Can Change Selection

- ESD exact per-emotion English file counts after actual licensed download.
- CREMA-D exact per-emotion distribution (current emergency/normal counts are estimated).
- Final downstream usage boundary (internal research only vs commercial deployment).

## 5) Risks And Limitations

- See: `risk_and_limitations_2026w14.md` (speaker bias, license constraints, domain shift).
