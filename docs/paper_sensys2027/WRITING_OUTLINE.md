# SenSys 2027 Draft Outline

This folder is a cleaned local draft for the paper. The current goal is not to present a finished single-platform UAV system, but to develop a convincing SenSys story around a future-facing voice safety layer for small nearby robots, with current drone experiments as the first concrete instantiation.

## Format Checklist

- Use `acmart` with `\documentclass[sigconf,anonymous]{acmart}`.
- Keep the paper in ACM two-column `sigconf` format.
- Maintain strict anonymization.
- Treat the body budget as `12` pages for the main paper; references can spill past the limit.
- Do not add custom formatting that shrinks margins, changes font size, or suppresses anonymity cues.

Reference: `https://sensys.acm.org/2017/cfp/`

## Recommended Storyline

- Main claim: in a future world where drones and small robots operate around people, voice should function as a lightweight safety mechanism that keeps robots interruptible and socially usable.
- Problem framing: this is not ``ASR on a drone'' and not ``one Tello demo''; it is an on-device safety-layer problem under severe self-noise.
- Main technical hook: narrow spoken-intent abstraction plus noise-robust training and explicit rejection of uncertain audio.
- Main systems hook: prototype integration, latency, false-trigger behavior, and cross-platform real-world validation matter as much as classifier accuracy.
- De-emphasize for now: multilingual generalization claims, stats-branch novelty, and any wording that makes the paper sound tied to a single airframe.

## Section Plan

1. `Introduction`
   Start from future human-robot co-presence and motivate voice as a safety mechanism, then narrow to rotor-noisy drones as the hardest current instantiation.

2. `Background and Motivation`
   Keep rotor-noise discussion and a short explanation of why intent-level modeling is the right scope.

3. `System Design`
   Show the onboard pipeline, command taxonomy, safety boundary, and why the abstraction is platform-agnostic.

4. `Training and Implementation`
   Center this section on the strongest completed recipe:
   preprocessing + class-aware augmentation + teacher-student transfer.

5. `Prototype and Real-World Setup`
   This is where the paper becomes a SenSys paper rather than a model paper. Do not bind the story to Tello; treat each platform as an instantiation of the same safety-layer design.

6. `Evaluation`
   Lead with completed benchmark results. Then add real-world and latency evidence as hard gates for the next round.

7. `Related Work`
   Keep concise and clearly separated into UAV interfaces, spoken intent understanding, robust transfer, and datasets.

## Evidence Status

- Ready to write as main evidence:
  `weeklyresult/weekly_drone_2026w14/preprocess_ext`
  `weeklyresult/weekly_drone_2026w14/branch_trial`

- Usable as supporting comparison:
  `weeklyresult/weekly_drone_2026w15/E0`
  `weeklyresult/weekly_drone_2026w15/E2_newTS_gpu3`

- Keep secondary for now:
  cross-language emergency analysis in `analysis/cross_language_emergency/...`

- Still missing before a serious submission draft:
  onboard latency, memory footprint, false-trigger analysis, real-world rotor-noise protocol, and prototype photos/stack figure.

## Writing Rules For The Next Round

- Every claimed contribution must map to a completed figure, table, or protocol.
- Avoid intro wording that sounds like the work is already ``done'' in a closed form; use current experiments as validation of a broader systems direction.
- If a result is exploratory, say so and keep it out of the contribution list.
- Prefer one strong story over two half-supported stories.
- For SenSys, the paper will be judged on system clarity and evaluation discipline, not only on model novelty.
