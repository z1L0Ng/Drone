# Meeting 2026-08-13 — Multilingual three-class retraining

## Objective

Prepare and, only after all gates pass, execute a clean-slate multilingual
three-class retraining study using English GSC v2, Spanish MSWC 1.0, and German
MSWC 1.0.

The model output remains exactly:

1. `emergency`
2. `movement`
3. `unknown`

Dataset-native words remain provenance and sampling fields. They are not model
outputs.

## Management decisions frozen on 2026-08-12

- Spanish and German are both in the next-stage scope.
- `alto`, `halt`, and `los` are dictionary-backed,
  Management-provisional engineering mappings. They are not native-validated
  semantic-equivalence claims.
- Spanish and German cardinal numbers zero through nine form the conservative
  phase-1 spoken-unknown allowlist.
- GSC v2 and MSWC 1.0 may be used under their recorded public-license terms;
  the MSWC no-reidentification condition is mandatory.
- The primary study is clean only. No SNR/noisy, teacher/student, fine-grained,
  language-head, hierarchical-head, control-loop, or flight lane is authorized.
- Prepared training defaults are three seeds (`0,1,2`), 50 maximum epochs,
  batch 32, Adam `1e-4`, validation macro-F1 selection, and validation-only
  scalar-temperature calibration.

## Work status

| ID | Work | Owner | Status | Receipt |
|---|---|---|---|---|
| M33-01 | Spanish/German lexical and metadata audit | Dataset | COMPLETE | source commit `14771ddb1a321c8858565f3dd233526deb4264a6` |
| M33-02 | Three-class metadata intake and split-feasibility tooling | Dataset | COMPLETE | 9 synthetic tests; metadata proposal only |
| M33-03 | Manifest-driven clean-slate training pipeline | Baseline | COMPLETE | source commit `1a261df80ac12729d0820cb089372c01e39b1c2e` |
| M33-04 | Joint integration validation | Management | SUPERSEDED | earlier integration commit `8893f26a`; 19/19 tests passed before the bridge |
| M33-05 | Official-source acquisition, metadata bootstrap, audio materialization, and frozen-manifest producer | Dataset | COMPLETE | source commit `96b0a452`; 34/34 tests pass; no real download |
| M33-06 | Final integration, push, server task, and unique tmux session | Management | IN PROGRESS | integrated bridge commit `c2948229`; final W33 commit pending |
| M33-07 | Server acquisition, preflight, and clean-slate training | Server task | AUTHORIZED, NOT STARTED | execute S0-S3 sequentially and fail closed at each gate |

## Hard gates before server training

- [x] The official-source acquisition script has a print-only receipt and
      explicit execution guard.
- [ ] GSC v2 and MSWC 1.0 archive identities, licenses, URLs, sizes, and hashes
      are recorded on the server.
- [ ] Derived audio is mono PCM 16 kHz and exactly 16,000 samples with raw to
      derived lineage and QC receipts.
- [ ] One frozen EN/ES/DE JSONL manifest contains four splits:
      `train`, `validation_selection`, `validation_calibration`, and `test`.
- [ ] Speaker/source-family isolation overlap and duplicate-group overlap are
      both zero.
- [ ] The Dataset-owner validation receipt is accepted by the Baseline
      consumer at the exact integration commit.
- [ ] The branch is pushed and the server checks out the exact full SHA in a
      clean worktree.
- [ ] Server disk/GPU/conda/CUDA/TensorFlow preflight passes.
- [ ] The unique server Codex task is bound to tmux session
      `weekly_drone_2026w33_multilingual_es_de`.

## Required comparison lanes

1. English-only development anchor, evaluated once on the common sealed
   EN/ES/DE test manifest.
2. EN+ES+DE naive pooled diagnostic baseline.
3. EN+ES+DE language/class/word/speaker-aware balanced main lane.

All lanes share the same frontend, model, clean-slate initialization, seeds,
budget, selection, calibration, and sealed test. Because English and
Spanish/German come from different source datasets, completed results must be
reported as pooled-source multilingual training results, not causal language
effects.

## Meeting-ready status

The project is ready to present the protocol and implementation plan at the
2026-08-13 meeting. It is not yet ready to present multilingual performance or
to claim that server training has started.
