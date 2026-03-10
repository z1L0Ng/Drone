# This Week TODO (Chicago Time, Deadline: Thursday 2026-03-12)

## Goal
- Complete this week's distillation iteration by Thursday 2026-03-12 (America/Chicago).
- Execution order for this week:
  1. Emergency data generation logic (higher pitch + higher loudness)
  2. Discuss and lock Teacher-Student strategy (today)
  3. Start server training tonight and check results tomorrow
  4. Only if results are weak, try a larger teacher model
  5. Keep local coding and server training fully synchronized via git checkpoints

## 1) Emergency Data Generation Logic (Highest Priority)
- [ ] Locate and confirm current data generation / augmentation entry points:
  - `src/data_pre.py`
  - `src/visual.py`
  - Any training-time augmentation hooks used by KD scripts
- [ ] Define class-conditional augmentation policy:
  - emergency: higher pitch + higher loudness
  - movement, unknown: normal speaking style (no aggressive pitch/loudness boost)
- [ ] Implement deterministic + configurable controls (seed + ranges):
  - pitch shift range for emergency
  - loudness gain range for emergency
  - keep non-emergency ranges neutral/small
- [ ] Add a quick verification script/output:
  - print/save per-class augmentation stats
  - export a few before/after waveforms for manual sanity check
- [ ] Run a small local smoke test to verify no data pipeline break

## 2) Teacher-Student Strategy + Loss Update
- [ ] Ensure input setup is explicit and fixed:
  - Teacher trains on clean audio only
  - Student trains on noisy audio
  - Student target includes matching teacher embedding representation
- [ ] Update KD objective variants:
  - embedding loss only
  - embedding loss + cross entropy
  - embedding loss + KL distillation + cross entropy
- [ ] Make variant switch configurable (single flag/env var)
- [ ] Reuse current scripts for controlled comparison:
  - `src/train_logmel_kd.py`
  - `scripts/run_kd_ablation_all.sh`
- [ ] Confirm final training command with advisor discussion before launch
- [ ] Save outputs in separate run directories and summarize metrics in one table

## 3) Larger Teacher Model (Conditional Fallback)
- [ ] Trigger condition: baseline run result is not good enough on key metrics (check on Wed 2026-03-11)
- [ ] If triggered, pick 1 practical larger teacher candidate
- [ ] Implement embedding extraction adapter (teacher -> current student embedding space)
- [ ] Run one fallback distillation experiment
- [ ] Compare vs current teacher on emergency-focused metrics first

## 4) Git Sync Workflow (Local Coding + Server Training)
- [ ] Before coding each session:
  - `git fetch --prune origin`
  - `git pull --ff-only origin main`
- [ ] Use focused commits by stage:
  - Commit A: emergency augmentation logic
  - Commit B: KD loss variants + ablation wiring
  - Commit C: stronger teacher integration scaffold/experiment
- [ ] Before server training:
  - push branch with clear tag/message
  - server `git pull --ff-only`
  - log exact commit SHA in training log filename
- [ ] After each training run:
  - sync result summary to repo (`result/...` + short markdown summary)
  - avoid committing large checkpoints unless needed

## Suggested Timeline (America/Chicago)
- Tuesday 2026-03-10 (today):
  - Finish emergency augmentation changes + smoke validation
  - Discuss and lock Teacher-Student training strategy
  - Launch server training tonight (after strategy confirmation)
- Wednesday 2026-03-11:
  - Review overnight results and produce comparison summary
  - If results are weak, start larger-teacher fallback experiment
- Thursday 2026-03-12:
  - Finish remaining experiments and finalize weekly report

## Definition of Done (This Week)
- [ ] Emergency class has clearly stronger pitch/loudness policy than other classes
- [ ] Teacher-Student strategy is confirmed before nightly server training
- [ ] Three KD loss variants are runnable and compared with consistent setup
- [ ] Teacher clean / student noisy setting is explicitly enforced in code
- [ ] Larger-teacher trial is completed if and only if baseline results are unsatisfactory
- [ ] Local/server git sync checkpoints are followed and recorded
