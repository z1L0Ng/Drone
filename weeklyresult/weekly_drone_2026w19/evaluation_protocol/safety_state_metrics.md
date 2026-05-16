# Safety-State And Bridge Metrics

Date: 2026-05-16

Scope: metric planning only. This file does not edit Tello control code, change ESP32 firmware, run live hardware, or claim flight safety.

## Safety-State Contract

The paper should evaluate the voice layer as an event source connected to a conservative bridge. The bridge is the safety boundary.

| Recognizer output | Safety-state meaning | Expected bridge behavior | Must not do |
| --- | --- | --- | --- |
| `emergency` | safety-critical handling | enter or request `SAFE_HOLD` / emergency handling, record command intent, log ack/timeout | silently ignore high-confidence emergency without logged reason |
| `movement` | pending ordinary interaction | enter `INTENT_PENDING`, require policy/manual override, record no direct movement command | map coarse `movement` directly to forward/back/left/right |
| `unknown` | fallback/no-action | keep or enter fallback/no-action/safe-hold, log rejection reason | treat unsupported audio as a movement or emergency command without confidence/policy |
| silence/background | no speech or non-command audio | no event, or fallback/no-action if an event is produced | produce repeated actionable commands |
| repeated speech | repeated user input | rate-limit, refractory handling, or repeated logged decisions | command spam without state checks |

## Existing Bridge Evidence

Current usable evidence is limited:

| Evidence | Path | What it supports | Missing |
| --- | --- | --- | --- |
| W18 local CDC replay dry-run | `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_report.md` | dry dispatch mechanics, movement blocked as pending, unknown rejected/safe-held, safety fields present | no live speech, no emergency event, no physical drone, no no-prop/grounded ack |
| W18 replay summary | `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_summary.json` | `total_events=30`, `movement_seen=1`, `emergency_exercised=0`, `error_count=0`, `flight_go_no_go=NO-GO` | does not validate emergency handling |
| W18 dry-run command log | `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_dry_command_log.csv` | required fields exist: `safety_hold`, `manual_override`, `command_result`, `result_detail` | replay only |
| W18 gate/buffer decision note | `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/decision_note.md` | gate remains feasibility prototype | no validated gate false-trigger evidence |

Use this evidence as plumbing support only. It is not validated safety behavior and not flight evidence.

## Quantitative Metrics

### Event And Schema Completeness

| Metric | Definition | Target for paper-facing run |
| --- | --- | --- |
| event_schema_completeness | fraction of rows containing required fields | `1.0` |
| required_timing_completeness | fraction of rows with capture/frontend/infer/total and host time where applicable | `1.0` |
| required_safety_field_completeness | fraction of rows with `safety_hold`, `manual_override`, `command_result`, `result_detail`, `ack/timeout` | `1.0` |
| evidence_type_completeness | fraction of rows labeled dry-run/no-prop/grounded/flight | `1.0` |

### Emergency Handling

| Metric | Definition | Paper meaning |
| --- | --- | --- |
| emergency_event_recall | `emergency` trials producing an emergency model event / total labeled emergency trials | recognizer plus live condition coverage |
| emergency_safe_hold_success_rate | emergency events that enter safe-hold/emergency state / emergency events | bridge behavior |
| emergency_command_ack_rate | emergency command records with ack / emergency command records | command path behavior |
| emergency_timeout_rate | emergency command records that timeout / emergency command records | command path risk |
| emergency_missed_safe_action_count | emergency trials with no safe-hold/no-action explanation | failure count |

### Movement Pending Interaction

| Metric | Definition | Paper meaning |
| --- | --- | --- |
| movement_event_recall | movement trials producing movement events / labeled movement trials | recognizer live coverage |
| movement_pending_correctness | movement events that enter `INTENT_PENDING` / movement events | bridge state correctness |
| direct_movement_block_rate | movement events not mapped directly to directional Tello commands / movement events | safety boundary proof |
| manual_override_coverage | movement events with explicit manual override state recorded / movement events | auditability |
| unsafe_movement_command_attempt_count | coarse movement events that attempt directional movement without policy/manual source | must be zero |

### Unknown And Background Fallback

| Metric | Definition | Paper meaning |
| --- | --- | --- |
| unknown_fallback_correctness | unknown events that become fallback/no-action/safe-hold / unknown events | unsupported audio containment |
| unknown_false_actionable_rate | unknown or background trials producing emergency/movement action attempt / unknown or background trials | safety risk indicator |
| silence_false_trigger_rate | silence/background windows producing any model event / silence/background windows | trigger/gate quality |
| no_action_success_rate | unknown/background events with `noop`, safe-hold, or rejection reason / unknown/background events | bridge rejection behavior |

### System And Log Health

| Metric | Definition | Paper meaning |
| --- | --- | --- |
| dry_error_rate | rows with `dry_error` or equivalent / total rows | dry-run reliability |
| ack_timeout_rate | timeout rows / command rows | command path reliability |
| state_transition_validity | rows matching the allowed transition table / total rows | state-machine correctness |
| repeated_trigger_rate | repeated actionable events within refractory window / total trials | gate/repetition behavior |
| unsafe_command_attempt_count | any command attempt violating policy | must be zero in accepted runs |

## Allowed Transition Table

Use this as the first validation oracle for bridge logs.

| Case | Allowed state before | Expected state after | Expected command result | Required fields |
| --- | --- | --- | --- | --- |
| emergency | any non-terminal state | `SAFE_HOLD` or `EMERGENCY_HANDLING` | dry/no-prop/grounded safe action or logged no-action reason | `safety_hold=true`, `command_result`, `ack/timeout` |
| movement | `IDLE`, `SAFE_HOLD`, or previous pending state | `INTENT_PENDING` or hold with reason | `dry_blocked`, `dry_noop`, or manual-approved pending path | `manual_override`, `result_detail` |
| unknown | any state | unchanged safe state or `SAFE_HOLD` | `noop` or reject/fallback | `fallback_reason` or `result_detail` |
| silence/background | any state | unchanged, no event, or fallback | no command | event/no-event accounting |
| repeated speech | any state | valid repeat or refractory state | no command spam | repeat window and reason |

## Mechanism-Level Comparison Metrics

When comparing against manual stop, controller action, geofencing, obstacle avoidance, return-to-home, or RC failsafe, do not use classifier accuracy/F1. Use a mechanism matrix:

| Axis | Voice safety layer | Existing mechanism comparison |
| --- | --- | --- |
| trigger source | human speech under rotor noise | position, obstacle perception, link/battery state, controller input |
| response path | recognizer event -> bridge state -> command/log | module trigger -> autopilot/controller state |
| coverage | emergency/movement/unknown speech events | spatial, obstacle, navigation, failsafe, or operator-action faults |
| response time | speech onset/model event to command/ack | module trigger to safe state |
| fail-safe behavior | fallback/no-action, safe-hold, manual override | hold, avoidance, RTH, landing, link failsafe |
| evidence type | offline/live speech, dry/no-prop/grounded/flight logs | module logs, vendor docs, controlled bench tests |

The paper can quantify each mechanism's own latency if logs exist, but should explain that there is no unified quantitative benchmark because the triggers, fault models, and success semantics differ.

## Required Future Evidence Before Claims

| Claim | Required evidence | Current status |
| --- | --- | --- |
| Bridge handles emergency path | live or replayed `emergency` cases with safe-hold/emergency state and no unsafe command | missing in W18 dry replay |
| Movement is safely mediated | movement cases showing no direct directional command without policy/manual override | partial dry replay support |
| Unknown is contained | unknown/background cases showing fallback/no-action and no unsafe command | partial dry replay support |
| Gate/buffer is controlled | silence/background, speech trigger, repeated speech, and false-trigger accounting | preliminary only |
| No-prop/grounded command behavior | logs with command send, ack/timeout, evidence type, manual override | not yet collected |
| Flight safety | approved flight protocol, instrumentation, risk controls, logs | not approved and not claimed |
