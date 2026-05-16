# Response-Time Metric Plan

Date: 2026-05-16

Scope: metric design only. This file does not run ESP32/Tello experiments and does not assume the current ESP32 path satisfies `<=1s` real-time inference.

## Timing Vocabulary

Use a single event-clock vocabulary across voice, manual, controller, and safety-module comparisons. Every result table should state which intervals were measured.

| Symbol | Event | Source |
| --- | --- | --- |
| `t_cue` | visual/verbal hazard or command cue shown to participant/operator | study script or experiment controller |
| `t_speech_onset` | first acoustic onset of the intended utterance | audio annotation or synchronized video/audio |
| `t_speech_offset` | end of utterance | audio annotation |
| `t_capture_start` | ESP32 audio window starts | firmware/host log |
| `t_capture_end` | ESP32 audio window ends | firmware log or derived from capture start and sample count |
| `t_frontend_done` | log-mel frontend finishes | firmware log |
| `t_infer_done` | TFLM `Invoke()` finishes | firmware log |
| `t_model_event_sent` | ESP32 status/event is serialized | firmware log |
| `t_model_event_host` | host receives model event | host log |
| `t_bridge_decision` | host safety-state bridge selects state/action | bridge log |
| `t_command_send` | host sends command or records dry-run command | bridge/Tello log |
| `t_ack_or_timeout` | command acknowledgement or timeout is recorded | bridge/Tello log |
| `t_physical_response` | drone-side physical response is observed | no-prop/grounded/flight instrumentation, if approved |

The current W17/W19 timing evidence measures capture, frontend, TFLM invoke, firmware total, and host elapsed. It does not measure speech onset because the existing stability run is trigger-based, not an annotated live speech study.

## Primary Response-Time Intervals

| Interval | Formula | Meaning | Current evidence |
| --- | --- | --- | --- |
| Human reaction to speech onset | `t_speech_onset - t_cue` | How quickly a person starts speaking after a cue | Protocol only |
| Voice event latency | `t_model_event_host - t_speech_onset` | End-to-end speech-to-model-event path | Protocol only for onset; existing runtime gives component timing after trigger |
| Capture latency | `t_capture_end - t_capture_start` | Audio window duration | Existing p50 about `926 ms` in W17/W19 timing |
| Frontend latency | `t_frontend_done - t_capture_end` | Feature extraction time | Existing p50 `55 ms` |
| Inference latency | `t_infer_done - t_frontend_done` | Pure TFLM `Invoke()` time | Existing p50 `2094 ms`; not `<=1s` |
| Device total | `t_model_event_sent - t_capture_start` | Firmware path through event generation | Existing p50 `3075 ms` |
| Host receive overhead | `t_model_event_host - t_model_event_sent` | USB/Bluetooth/status transport and host receive | Existing USB p50 about `5.5 ms`; Bluetooth not measured |
| Bridge decision latency | `t_bridge_decision - t_model_event_host` | Host safety-state policy time | Needs bridge logs |
| Model event to host command | `t_command_send - t_model_event_host` | Model-event-to-command path | Needs dry/no-prop/grounded logs |
| Command to ack | `t_ack_or_timeout - t_command_send` | Tello/control acknowledgement path | Needs dry/no-prop/grounded logs |
| Command to physical response | `t_physical_response - t_command_send` | Physical drone response | Future only; not valid from dry-run |

## Required Summary Statistics

For every response-time table, report:

- `n`
- p50, p90, p95, max
- timeout count and timeout definition
- dropped event count
- clock source and synchronization method
- whether the result is dry-run, no-prop, grounded, or flight
- whether human reaction time is included

Do not report a single "response time" number without stating the start and stop events.

## Voice Path Definition

For the voice safety layer, use two main paper metrics:

1. Interface-only response time:
   `t_command_send - t_speech_onset`

   This answers: after the user starts saying a command, how long until the system records a command decision or dry-run command?

2. End-user response time:
   `t_command_send - t_cue`

   This includes human reaction time and is useful when comparing how fast a user can use voice versus a controller after the same hazard cue.

For runtime-only evaluation, report the component budget separately:

```text
capture + frontend + TFLM invoke + report/transport + bridge decision + command send
```

Current evidence supports this runtime decomposition only after the host trigger. It does not yet support a speech-onset-to-command claim.

## Manual Stop And Controller Comparison

Manual stop/controller action can be compared fairly only when the trigger cue and end event are shared.

Recommended comparator protocol:

| Comparator | Start event | Stop event | Notes |
| --- | --- | --- | --- |
| Voice emergency | same hazard cue `t_cue`; also annotate `t_speech_onset` | `t_command_send`, `t_ack_or_timeout`, optional `t_physical_response` | Report both cue-to-command and speech-onset-to-command. |
| Manual stop button | same hazard cue `t_cue` | button press logged, command send, ack/timeout | Includes human reaction and hand/controller access time. |
| Controller stick/switch | same hazard cue `t_cue` | controller input logged, command send, ack/timeout | Use a predefined action such as stop/hover; do not compare to movement phrases. |
| Host keyboard emergency | same hazard cue `t_cue` | host keypress logged and dry/no-prop command record | Useful lab baseline. |

Do not compare a voice utterance beginning at `t_speech_onset` against a manual comparator beginning at `t_cue`; that would exclude voice human reaction time but include manual reaction time. For interface-only latency, start all methods at the first method-specific input event: speech onset, button down, stick movement, or keypress.

## Existing UAV Safety-Module Comparison

Existing safety mechanisms should be compared at mechanism level, not as recognizer baselines.

| Mechanism | Trigger source | Fair latency start | Fair latency stop | Quantitative comparison allowed? |
| --- | --- | --- | --- | --- |
| Voice safety layer | user speech expressing intent | speech onset or model event, depending on metric | command decision, ack/timeout, or safe state | Yes within voice path; cross-mechanism only with careful trigger definitions. |
| Manual stop/controller | operator physical action | hazard cue for user-level comparison, or button/stick input for interface-only comparison | command send, ack/timeout, safe state | Yes if same cue/end event is used. |
| Geofencing | GPS/position boundary violation | geofence violation event | hold/RTH/limit action recorded | Mechanism latency only; not classifier accuracy. |
| Obstacle avoidance | proximity/perception detection | obstacle detection event | avoidance/stop command or state | Mechanism latency only; trigger and fault type differ from voice. |
| Return-to-home | link loss, battery, operator command, or policy condition | RTH trigger event | RTH state entered or command ack | Mechanism latency only; not an emergency speech comparator. |
| RC failsafe | link loss or controller failsafe condition | failsafe trigger | failsafe state entered | Mechanism latency only; not comparable by F1. |

The paper should explain that these mechanisms are complementary layers with different sensors, triggers, and action semantics. The fair comparison is a matrix over trigger source, coverage, response path, latency definition, fail-safe behavior, and evidence type.

## Instrumentation Requirements

Future runtime and bridge runs should log at least:

| Field | Required for |
| --- | --- |
| `run_id`, `trial_id`, `case_id` | join across logs |
| `expected_label`, `pred_label`, `confidence` | recognizer and bridge analysis |
| `capture_ms`, `frontend_ms`, `infer_ms`, `total_ms` | runtime budget |
| `host_elapsed_ms` | transport/host overhead |
| `speech_onset_ms` or absolute `t_speech_onset` | speech-to-event time |
| `event_host_time` | model event host receipt |
| `state_before`, `state_after` | safety-state behavior |
| `safety_hold`, `manual_override` | bridge safety gates |
| `command_intent`, `tello_command`, `command_mode` | command boundary |
| `command_result`, `result_detail` | action outcome |
| `ack_time`, `timeout_ms`, `ack_or_timeout` | command response |
| `evidence_type` | dry-run, no-prop, grounded, flight |

## Paper Claim Rules

- Current `infer_p50_ms=2094` is pure TFLM invocation time and should be reported as a bottleneck, not hidden inside total latency.
- Current `total_p50_ms=3075` should be described as board/host event-path runtime, not speech-onset response time.
- The paper cannot claim `<=1s` real-time onboard inference from the current checkpoint.
- Dry-run command records can support bridge logic and logging behavior, not physical drone response.
- Command-to-drone-response latency requires no-prop, grounded, or flight instrumentation and must be labeled by evidence type.
