# User Study And Live Evidence Protocol

Date: 2026-05-16

Scope: protocol only. Do not collect participants, record audio, or run hardware under this plan until the manager explicitly approves data collection and ethics/privacy handling.

## Goal

The user study should test whether ordinary users can express the intended voice-command UAV safety-layer states under controlled acoustic conditions. It should not be framed as proof of live-flight safety. The study supports user-study/demo evidence and provides labeled live audio for recognizer and timing evaluation.

The study must keep the current semantic contract:

| Label | Paper meaning | Bridge meaning |
| --- | --- | --- |
| `emergency` | safety-critical handling | eligible for safe-hold, stop, or operator escalation |
| `movement` | pending ordinary interaction | not a direct flight command; requires policy/manual override |
| `unknown` | fallback/no-action | unsupported or ambiguous audio should not affect control |

## Participant Count

Recommended main study:

- `24` participants for the first paper-facing live study.
- Minimum pilot before main study: `6` participants, used only to debug script, timing, logging, and consent flow.
- Minimum acceptable system-evidence set if schedule is tight: `12` participants, but report it as a small controlled study, not broad population evidence.

Rationale:

- `24` participants gives enough participant-level spread to report median and interquartile ranges by condition without pretending to estimate population-wide performance.
- The project needs per-condition behavior and failure examples more than a high-powered human-factors claim.
- The study is a system validation protocol, not a clinical or broad demographic study.

## Participant Metadata

Collect only fields needed for analysis. Avoid names in analysis files.

Required fields:

| Field | Values or format | Purpose |
| --- | --- | --- |
| participant_id | anonymized ID such as `P001` | join audio/event logs without names |
| age_bucket | `18-24`, `25-34`, `35-44`, `45+`, prefer not to say | aggregate demographics |
| self_reported_gender | optional/free-form/prefer not to say | aggregate demographics only |
| primary_language | ISO or plain text | language/accent analysis |
| other_languages | optional list | language/accent analysis |
| accent_self_description | optional free-form | explain outliers conservatively |
| voice_interface_experience | none/occasional/frequent | interaction context |
| drone_experience | none/observed/piloted/frequent | task familiarity |
| speech_or_hearing_notes | optional/prefer not to say | interpret failures |
| consent_audio_recording | yes/no | required gate |
| consent_demo_video | yes/no | separate from audio |

Do not store personally identifying names in the analysis manifest. Voice recordings are sensitive data and should be handled as restricted artifacts unless the manager approves a release policy.

## Utterance Script

Use a fixed script so recognition and timing metrics are comparable across people. Randomize the order within each block.

Emergency utterances:

| ID | Utterance | Intended label |
| --- | --- | --- |
| E1 | stop | `emergency` |
| E2 | stop now | `emergency` |
| E3 | emergency stop | `emergency` |
| E4 | hold position | `emergency` |
| E5 | land now | `emergency` |
| E6 | abort mission | `emergency` |

Movement/pending-interaction utterances:

| ID | Utterance | Intended label |
| --- | --- | --- |
| M1 | move | `movement` |
| M2 | go forward | `movement` |
| M3 | move left | `movement` |
| M4 | move right | `movement` |
| M5 | come here | `movement` |
| M6 | follow me | `movement` |

These movement phrases are only labels for pending interaction. The bridge must not convert them directly into directional Tello commands without a separate approved policy path.

Unknown/out-of-contract utterances:

| ID | Utterance | Intended label |
| --- | --- | --- |
| U1 | hello drone | `unknown` |
| U2 | take a picture | `unknown` |
| U3 | what time is it | `unknown` |
| U4 | play music | `unknown` |
| U5 | this is not a command | `unknown` |
| U6 | continue the inspection | `unknown` |

Add silence/background windows as separate non-speech trials. They should be logged as `silence` in the study manifest and analyzed as no-event or fallback/no-action behavior, not as one of the three spoken labels unless the classifier emits a label.

## Study Conditions

Use a core block and an optional stress block.

Core block:

| Factor | Levels |
| --- | --- |
| participant count | `24` target |
| utterances | 18 scripted utterances |
| repetitions | 2 per utterance |
| distance | `1 m` |
| angle | front-facing `0 deg` |
| acoustic condition | quiet room, rotor playback/noise condition |

Core block count at target size: `24 participants * 18 utterances * 2 repetitions * 2 acoustic conditions = 1728 spoken trials`, plus silence/background trials.

Stress block, optional after core block is stable:

| Factor | Suggested levels | Notes |
| --- | --- | --- |
| distance | `0.5 m`, `2 m`, `3 m` | Use a 6-utterance sentinel set to control total time. |
| angle | `45 deg`, `90 deg`, optional `180 deg` | Use only if room layout and safety allow. |
| volume/style | conversational, raised, urgent | Record relative level or dBA. |
| background | office speech, fan/HVAC, outdoor ambient, rotor playback | Do not imply real rotor if using speaker playback. |

Sentinel set for stress block: `E1`, `E3`, `M2`, `M5`, `U2`, `U5`, plus silence/background windows.

## Environment Metadata

Every recording block should log:

| Field | Example |
| --- | --- |
| location_id | `lab_room_a` |
| room_type | quiet lab, office, hallway, outdoor |
| microphone/device | XIAO ESP32-S3 Sense, board serial if available |
| model_candidate | `B_small_teacher_student` or later approved candidate |
| firmware_commit_or_manifest | commit SHA or frozen firmware manifest |
| transport | USB CDC, Bluetooth, host microphone, offline playback |
| distance_m | numeric |
| angle_deg | numeric |
| background_condition | quiet, rotor playback, office speech, fan |
| noise_source | file path, playback device, live rotor if approved |
| approximate_spl_dba | measured or `not_measured` |
| trial_timestamp | UTC or local with timezone |
| operator_id | anonymized |

## Procedure

1. Consent and metadata.
   Confirm audio consent. Demo video requires separate consent.

2. Device and log setup.
   Record firmware/model manifest, transport, clock sync method, room condition, distance, and angle.

3. Calibration block.
   Record 5 seconds of background and 3 practice utterances. Do not include practice trials in paper results.

4. Core utterance block.
   Randomize the 18 utterances. For each trial, record trial ID, expected label, prompt ID, participant ID, acoustic condition, start cue, speech onset, model event, bridge decision if connected, and notes.

5. Silence/background block.
   Collect no-speech windows and background speech if approved. This is required for fallback/no-action evidence.

6. Optional stress block.
   Run sentinel utterances across distance/angle/volume/background levels. Stop if logging quality is poor.

7. Optional demo sequence.
   Record a short controlled demo showing `emergency`, `movement`, `unknown`, and manual override or fallback behavior. Label it as demo evidence only.

## Required Output Files After Approval

Do not create these from this planning task. They are future collection outputs.

| File | Contents |
| --- | --- |
| `participant_metadata.csv` | anonymized participant-level metadata |
| `utterance_manifest.csv` | trial ID, participant ID, utterance ID, expected label, condition fields |
| `audio_index.csv` | audio path, onset/offset labels, privacy status |
| `model_event_log.csv` | predicted label, confidence, timing, raw diagnostics |
| `bridge_event_log.csv` | state before/after, command intent, command result, manual override, ack/timeout |
| `timing_annotations.csv` | speech onset, speech offset, model event, host decision, command send, response |
| `study_summary.md` | results, exclusions, failure modes, claim boundary |

## Metrics

Recognizer/user-level metrics:

- per-class accuracy and macro F1 by participant and condition
- emergency recall and miss rate
- movement pending-detection rate
- unknown false accept rate
- silence/background false trigger rate
- confidence distributions and calibration notes

Timing metrics:

- speech onset to ESP32 model event
- ESP32 model event to host bridge decision
- host decision to command send or dry-run record
- command send to ack/timeout or observed drone-side state, only when a no-prop/grounded/flight protocol exists

Bridge metrics:

- emergency safe-hold success rate
- movement direct-command block rate
- manual override coverage
- unknown fallback/no-action correctness
- unsafe command attempt count
- ack/timeout rate

## Claim Boundary

The paper can claim a controlled user-study protocol only after collecting the above logs. It can claim participant-level live utterance results only from approved, labeled data. It cannot claim live-flight safety from a user study unless flight was separately approved, instrumented, and reported. A one-minute demo can help reviewers understand the system, but it should not be presented as a quantitative benchmark.
