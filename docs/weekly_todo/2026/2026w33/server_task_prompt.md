# W33 dedicated server task — multilingual three-class retraining

You are the only server-side Codex task for the Talk-to-Me Drone W33
multilingual run. Work only in `/files1/Zilong/Drone` and use the enclosing
tmux session `weekly_drone_2026w33_multilingual_es_de`. Do not create or reuse
another tmux session.

## Authorized objective

Execute the approved clean-slate three-class study with:

- English: Google Speech Commands v2;
- Spanish: MSWC 1.0;
- German: MSWC 1.0;
- model outputs exactly `emergency / movement / unknown`.

Dataset-native words are provenance and within-class sampling fields only.
`alto`, `halt`, and `los` are Management-provisional engineering mappings, not
native-language or paper equivalence claims. The Spanish/German spoken-unknown
allowlist is cardinal numbers zero through nine. Preserve all attribution and
license receipts and perform no re-identification or audio redistribution.

## Execution order

1. Verify the exact branch and 40-character commit supplied by Management,
   clean Git status, available disk/GPU, the `drone` Conda environment, and the
   fixed acquisition/config hashes. Stop on any mismatch.
2. Run the audio bridge in default dry-run mode and save the S0 plan receipt.
3. Under the already recorded Management authorization, set only the bridge's
   documented execution guards and acquire the pinned official GSC v2 and MSWC
   1.0 assets. Keep archive URL, size, HTTP, SHA-256, extraction, license, and
   no-reidentification receipts. Stop on any mismatch or unsafe member.
4. Build and freeze the four-way metadata proposal using
   `train / validation_selection / validation_calibration / test`, seed
   `20260812`, and globally grouped speaker plus source-family components.
5. Materialize content-addressed mono PCM 16 kHz, exactly 16,000-sample WAVs.
   Preserve raw-to-derived lineage and fail closed on decode, NaN, clipping,
   duration/boundary, hash, provenance, or duplicate failure.
6. Produce the Dataset-owner frozen 21-field JSONL manifest and validation
   receipt. Require all 36 language/class/split cells, zero speaker/source-family
   overlap, zero duplicate overlap, and successful load by the Baseline consumer.
7. Run `scripts/server/preflight_multilingual_2026w33.sh` at the exact commit.
   Do not open the sealed test for selection or calibration.
8. Run `scripts/server/run_multilingual_2026w33_all.sh` directly inside this
   existing tmux session (do not call the wrapper that creates another tmux).
   Execute the three frozen lanes and seeds 0, 1, and 2. Preserve start,
   completion/abort, checkpoint, environment, config, manifest, prediction,
   calibration, and metric receipts.

## Hard boundaries

- No legacy checkpoint, support, threshold, SNR/noisy result, or leaderboard.
- No teacher/student, fine-grained, language-specific, or hierarchical head.
- No paper, Notion, Gmail, firmware, hardware, control-loop, or flight changes.
- Do not edit tracked source after checking out the exact commit.
- Do not delete or overwrite existing data/results. Stop on output collision.
- English uses GSC while Spanish/German use MSWC; never describe source-stratified
  differences as causal language effects.

Write phase receipts under the configured W33 data/result roots and end with a
compact Management handoff containing exact paths, hashes, support, resource
use, completed/aborted runs, negative results, blockers, and the current tmux
status. If a phase fails, record the abort receipt and stop rather than weakening
any gate.
