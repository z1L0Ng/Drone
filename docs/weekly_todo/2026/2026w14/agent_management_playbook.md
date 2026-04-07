# 2026w14 Multi-Agent Management Playbook

## Purpose
- Keep execution parallel while preserving one source of truth in weekly docs.
- Separate responsibilities strictly:
  - Manager agent (this thread): planning, documentation, acceptance, and coordination.
  - Acoustic agent: dataset scouting and acoustic analysis only.
  - Model agent: model/config branch work and training setup only.
  - Server operator: training execution and log/result handoff only.

## Workstream Ownership
| Workstream | Owner | Must Deliver | Must Not Touch |
|---|---|---|---|
| Dataset scouting + acoustic features | Acoustic agent | `dataset_options_2026w14.md`, `dataset_manifest_2026w14.csv`, acoustic figures and findings | `docs/weekly_todo/*`, `TODO_THIS_WEEK.md`, `docs/technical_spec/*` |
| Model branch design + config | Model agent | `preprocess_ext` / `branch_trial` run commands, config diff, risk note | Notion checklist and weekly management docs |
| Server training execution | Server operator | PID/LOG startup receipt; completion receipt with checkpoint+result+log tail | Local weekly docs |
| Weekly status + meeting package | Manager agent | `todo.md`, `handoff_log.md`, Notion checklist, wrap-up docs | Acoustic/model implementation |

## Dispatch Prompts
### Acoustic Agent Prompt
- Objective: first return dataset options and sample counts for emergency/normal/multilingual validation.
- Phase 1 outputs:
  - `analysis/cross_language_emergency/dataset_options_2026w14.md`
  - `analysis/cross_language_emergency/dataset_manifest_2026w14.csv`
- Phase 2 (only after PI selection):
  - `alpha_ratio.png`
  - `spectral_centroid_bandwidth.png`
  - `energy_distribution.png`
  - `pitch_energy_envelope.png`
  - `findings.md`
  - `summary_2026w14.md`

### Model Agent Prompt
- Objective: prepare executable and auditable setup for `preprocess_ext` and `branch_trial`.
- Required outputs:
  - launch commands
  - config delta from baseline
  - expected output paths
  - risk and fallback notes

### Server Operator Prompt
- Objective: run training only, with strict receipt format.
- Startup receipt (within 10 min):
  - PID
  - LOG path
  - first 30 log lines
- Completion receipt:
  - checkpoint path
  - result directory tree
  - last 50 log lines

## Server Orchestration
1. Run order: `preprocess_ext` then `branch_trial` (serial by default).
2. Force weekly tag: `WEEKLY_TAG=drone_2026w14`.
3. Required paths:
   - `saved_models/weekly_drone_2026w14/{preprocess_ext,branch_trial}/`
   - `result/weekly_drone_2026w14/{preprocess_ext,branch_trial}/`
   - `logs/weekly_drone_2026w14_{task}_*.log`

## Acceptance Gate
- Evidence complete means checkpoint + result + log all exist.
- Every update must be reflected in both:
  - `docs/weekly_todo/2026/2026w14/todo.md`
  - `docs/weekly_todo/handoff_log.md`
- Notion checklist state must match repo state.
