# SenSys 2027 Draft Outline

This folder is a cleaned Overleaf-style working draft for the paper. It is organized around the claims that are already supported in the repository instead of the older placeholder structure from the uploaded zip.

## Format Checklist

- Use `acmart` with `\documentclass[sigconf,anonymous]{acmart}`.
- Keep the paper in ACM two-column `sigconf` format.
- Maintain strict anonymization.
- Treat the body budget as `12` pages for the main paper; references can spill past the limit.
- Do not add custom formatting that shrinks margins, changes font size, or suppresses anonymity cues.

Reference: `https://sensys.acm.org/2017/cfp/`

## Recommended Storyline

- Main claim: rotor-noisy UAV voice control is best framed as an on-device intent-recognition problem with emergency-aware evaluation.
- Main technical hook: class-aware noise training plus clean-to-noisy teacher-student transfer.
- Main systems hook: prototype integration, latency, and false-trigger behavior matter as much as classifier accuracy.
- De-emphasize for now: multilingual generalization claims and stats-branch novelty until their ablations are cleaner.

## Section Plan

1. `Introduction`
   Focus on the systems problem, not just speech robustness.

2. `Background and Motivation`
   Keep rotor-noise discussion and a short explanation of why intent-level modeling is the right scope.

3. `System Design`
   Show the onboard pipeline, command taxonomy, and safety boundary.

4. `Training and Implementation`
   Center this section on the strongest completed recipe:
   preprocessing + class-aware augmentation + teacher-student transfer.

5. `Prototype and Real-World Setup`
   This is where the paper becomes a SenSys paper rather than a model paper.

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
- If a result is exploratory, say so and keep it out of the contribution list.
- Prefer one strong story over two half-supported stories.
- For SenSys, the paper will be judged on system clarity and evaluation discipline, not only on model novelty.
