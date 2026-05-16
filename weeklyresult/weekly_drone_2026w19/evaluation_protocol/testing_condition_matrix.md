# Testing Condition Matrix For UAV Voice Safety-Layer Evaluation

Date: 2026-05-16

Scope: evaluation design only. This file does not train models, start server work, collect new data, edit paper tex, edit ESP32 firmware, or edit Tello control code.

## Evaluation Evidence Tiers

The SenSys evaluation should be organized into four evidence tiers. Tables and figures should not mix claims across tiers.

| Tier | What it evaluates | Primary metrics | Claim boundary |
| --- | --- | --- | --- |
| Recognizer quality | Whether the recognizer maps audio to `emergency`, `movement`, and `unknown` under matched test conditions. | accuracy, macro F1, per-class precision/recall/F1, emergency recall, unknown false accept rate, confusion matrix | Supports intent-recognition quality only. It is not bridge behavior, runtime feasibility, or safety validation. |
| Latency/runtime | Whether the deployment path can produce an event with measured timing and acceptable stability. | capture/frontend/infer/report p50 and p95, success/drop rate, timeout rate, TFLite size, op compatibility | Supports runtime evidence only. Existing `2094 ms` inference p50 and `3075 ms` total p50 do not satisfy a `<=1s` real-time claim. |
| Safety-state/bridge behavior | Whether events are converted into conservative states and logged command decisions. | safe-hold success, fallback correctness, direct movement block rate, manual override coverage, ack/timeout rate, unsafe command attempts | Supports dry-run/no-prop/grounded behavior only at the evidence level actually measured. It is not flight safety unless flown under an approved protocol. |
| User-study/demo evidence | Whether people can issue the intended utterances under controlled conditions and whether the system path is understandable. | participant-level accuracy, per-condition event success, speech-onset-to-event time, subjective workload/confidence if collected, demo coverage | Requires real collection and consent. A demo is explanatory evidence, not a statistical benchmark unless the protocol is executed and logged. |

## Existing Evidence Snapshot

Local repo evidence already supports a limited recognizer/runtime story:

| Evidence | Path or source | Usable now? | Notes |
| --- | --- | --- | --- |
| Anchor recognizer noisy-set result | `weeklyresult/weekly_drone_2026w14/preprocess_ext/classification_report_noisy.txt` | Yes | Accuracy `0.88`, macro F1 `0.88`, support `9984`. This is the model-quality anchor. |
| Embedded student noisy-set result | `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/classification_report_noisy.txt` | Yes | Accuracy `0.87`, macro F1 `0.87`, support `9984`. Use as deployment candidate, not winner. |
| ESP32 runtime stability | `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md` | Yes, runtime only | 30 triggers, success `1.0000`, drop `0.0000`, inference p50 `2094 ms`, total p50 `3075 ms`. Not semantic accuracy or safety validation. |
| W19 ESP32 latency audit | `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/*` | Yes, runtime audit only | Confirms current `B_small_teacher_student` is not `<=1s` feasible through low-risk engineering-only changes. |
| W18 Tello dry-run replay | `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_report.md` | Yes, plumbing only | 30 replayed events, `movement=1`, `unknown=29`, no emergency case, dry-run only, flight `NO-GO`. |
| W19 first-batch baseline results | Branch `codex/track-d-baseline-results-20260514`, commit `91153291` | Cite as unmerged branch evidence only | TCResNet8 logmel: accuracy `0.8409`, macro F1 `0.8407`; BC-ResNet1 logmel: accuracy `0.7970`, macro F1 `0.7935`; DS-CNN-S logmel: accuracy `0.6066`, macro F1 `0.6007`; support `10008`, eval SNR `-10 dB`. Do not merge or treat as mainline evidence until approved. |

The W19 baseline branch support (`10008`) differs from the anchor/student support (`9984`). Any paper table that puts these in one leaderboard must first verify split, preprocessing, label encoder, and noise-mixing comparability. Until that audit is complete, cite the W19 results as first-batch baseline direction, not final paper numbers.

## Condition Matrix

| Condition group | Levels to test | Evidence tier | Metrics | Current evidence | Paper use |
| --- | --- | --- | --- | --- | --- |
| Offline split parity | Same `data_paths.npz`, same label encoder, same held-out split, same support count, same seed policy | Recognizer quality | accuracy, macro F1, per-class P/R/F1 | Anchor/student support `9984`; W19 branch baselines support `10008` | Required before final baseline table. |
| Recognizer families | Anchor `w14 preprocess_ext`, embedded student `B_small_teacher_student`, TCResNet8, BC-ResNet1, DS-CNN-S | Recognizer quality | same as above plus confusion matrix | Anchor/student on main; baselines on unmerged branch | Good first paper table after comparability audit. |
| SNR sweep | clean/no mix, `-5`, `-10`, `-15`, optional `-20 dB` stress | Recognizer quality | accuracy by SNR, emergency recall, unknown false accept rate, macro F1 | W19 baselines use eval `-10 dB` only; anchor needs matching sweep evidence | Quantitative robustness curve if generated from existing dataset. |
| Noise source | quiet/clean, offline `tellonoise`, rotor playback, real rotor/no-prop recording if approved | Recognizer quality and user-study/demo | per-source confusion matrix, event miss rate, false trigger rate | Offline `tellonoise` exists; rotor/live conditions not fully validated | Separate synthetic/offline, playback, and real rotor. Do not collapse them. |
| Speaker distance | `0.5 m`, `1 m`, `2 m`, `3 m` from board microphone | User-study/demo | per-distance accuracy, emergency recall, speech-onset-to-event time, missed event rate | Protocol only | Needs new collection approval. |
| Speaker angle | front `0 deg`, side `45 deg`, side `90 deg`, rear `180 deg` if safe/available | User-study/demo | per-angle accuracy and missed event rate | Protocol only | Useful for real-world interaction study, not current claim. |
| Speaking style/volume | conversational, raised voice, urgent/emergency style | User-study/demo | per-style emergency recall, false accept rate, onset detection reliability | Protocol only | Collect dBA or calibrated relative level if possible. |
| Background environment | quiet room, office background speech, fan/HVAC, outdoor ambient, rotor playback | User-study/demo and recognizer quality | per-condition accuracy/F1, unknown false accept, false trigger rate | Protocol only except offline noise | Use as condition table after approval. |
| Utterance class | emergency, movement/pending interaction, unknown/out-of-contract, silence/background | All tiers | class metrics plus state-transition validity | Offline labels exist; live silence/background only partly covered by gate work | Required for every end-to-end protocol. |
| Runtime path | desktop float, desktop int8, board int8 over USB CDC, future Bluetooth if implemented | Latency/runtime | fidelity agreement, p50/p95 capture/frontend/infer/report, drop/timeout | Board USB CDC exists; Bluetooth not measured | Runtime comparison, not recognizer accuracy. |
| Bridge event path | emergency, movement, unknown, silence/background, repeated speech | Safety-state/bridge | safe-hold, fallback correctness, direct movement block, manual override coverage, ack/timeout | W18 dry-run replay has movement/unknown only | Must collect live emergency and movement before bridge validation claim. |
| Manual response comparator | manual stop button/controller command from same visual or verbal cue | Latency/runtime and mechanism comparison | cue-to-command, command-to-ack, success/timeout | Protocol only | Fair response-time comparison if same cue and same logging method are used. |
| Existing safety mechanisms | geofencing, obstacle avoidance, return-to-home, RC failsafe/manual controller | Mechanism-level comparison | trigger source, response path, latency definition, coverage, fail-safe behavior, evidence type | Planning/motivation only | Mechanism matrix only. Do not treat as classifier baselines. |

## Recommended Baseline Expansion

The baseline comparison should expand from a single offline noisy accuracy/F1 table into three matched layers:

1. Matched offline recognizer baseline table.
   Include anchor, embedded student, TCResNet8, BC-ResNet1, and DS-CNN-S only after verifying common split/support and preprocessing. Report overall accuracy, macro F1, emergency precision/recall/F1, movement F1, unknown false accept rate, and confusion matrix.

2. Robustness-by-condition table or curve.
   Repeat the same recognizer set across SNR and noise-source conditions. If only one SNR exists, the paper should say it is a first-batch baseline at `-10 dB`, not a robustness curve.

3. Systems evidence table.
   Separately report deployment feasibility, ESP32 timing, bridge state behavior, and user-study/demo evidence. These should not be mixed into the recognizer leaderboard.

## Quantitative Vs Mechanism-Matrix Claims

Quantitative claims are defensible when the same input population, labels, trigger definition, and logging path are shared. Recognizer baselines can be compared quantitatively under matched offline conditions. Runtime paths can be compared quantitatively under the same device, firmware, and clock events. Bridge behavior can be quantified from event/state logs.

Existing UAV safety modules do not share the same trigger source or label space. Geofencing is triggered by position/airspace constraints, obstacle avoidance by proximity or perception, return-to-home by navigation/link/battery conditions, and RC/manual control by operator action. They should be compared in a mechanism matrix using trigger source, response path, coverage, fail-safe behavior, and evidence type, with response time only compared from each mechanism's own trigger event.
