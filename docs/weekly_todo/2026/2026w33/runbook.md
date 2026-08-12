# W33 multilingual server runbook

This runbook becomes executable only after the acquisition/materialization
producer is integrated, the exact branch is pushed, and Management records the
full commit SHA. Commands containing placeholders must fail closed.

## Fixed names

```bash
WEEKLY_TAG=drone_2026w33
TMUX_SESSION=weekly_drone_2026w33_multilingual_es_de
RESULT_ROOT=weeklyresult/weekly_drone_2026w33
```

## Stage A — local integration

1. Integrate the Dataset intake, Dataset materialization, and Baseline commits
   on `codex/multilingual-es-de-w33`.
2. Run all synthetic tests in the `drone` conda environment.
3. Run shell syntax, config, manifest-producer/consumer compatibility, and
   print-only launch checks.
4. Commit W33 management receipts and push the exact branch.

No audio is downloaded during Stage A.

## Stage B — server project task and persistent session

Create one remote Codex project task for this project only. The task must:

- check out the exact pushed commit;
- record the server repo path, branch, and full SHA;
- use only tmux session `weekly_drone_2026w33_multilingual_es_de`;
- write acquisition/materialization receipts outside the Git worktree or under
  ignored data/result roots;
- report startup, phase transitions, blockers, and completion to Management.

Do not reuse an Acoustic, BSM, application, or older Drone session.

## Stage C — official-source acquisition

Run the integrated acquisition wrapper first in print-only mode. Review:

- official URL and release identity;
- license and MSWC no-reidentification receipt;
- required disk space;
- archive and extraction destinations;
- expected archive structure;
- resume behavior.

Only then set the acquisition execution guard and download on the server. Keep
archive byte hashes, HTTP metadata, and extraction inventory.

Use `/files1/Zilong/Drone_w33_multilingual_data` as the W33 data root. Execute
the bridge one stage at a time; never use `--stage all` for the first real run:

```bash
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /files1/Zilong/Drone_w33_multilingual_data

DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /files1/Zilong/Drone_w33_multilingual_data --stage S0 --execute

DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
DRONE_W33_SPLIT_FREEZE_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /files1/Zilong/Drone_w33_multilingual_data --stage S1 --execute
```

S1 includes official acquisition, metadata bootstrap, deterministic proposal,
and the Dataset-owned proposal-freeze receipt. Review its archives, tree
fingerprints, 105,829-row GSC gate, six MSWC CSV/locator checks, support, and
zero-overlap receipts before S2.

## Stage D — materialization and frozen manifest

Materialize all admitted rows to content-addressed mono PCM 16 kHz, 16,000
sample WAV files. Produce:

- raw-to-derived lineage;
- decode/resample/downmix/pad/crop and QC receipts;
- a frozen four-split JSONL manifest;
- a Dataset-owner validation receipt;
- per-language/class/split/word/speaker/source-family support;
- zero-overlap isolation and duplicate audits.

The manifest must pass both the Dataset validator and Baseline consumer before
training is authorized.

```bash
DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
DRONE_W33_AUDIO_TRANSFORM_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /files1/Zilong/Drone_w33_multilingual_data --stage S2 --execute

DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
DRONE_W33_MANIFEST_FREEZE_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /files1/Zilong/Drone_w33_multilingual_data --stage S3 --execute
```

## Stage E — training preflight

```bash
bash scripts/server/preflight_multilingual_2026w33.sh \
  <FULL_COMMIT_SHA> <FROZEN_MANIFEST_JSONL> \
  <VALIDATION_RECEIPT_JSON> <AUDIO_ROOT>
```

This preflight must verify the exact clean commit and all development audio.
It must not open sealed-test audio.

## Stage F — unique tmux launch

Review the rendered command:

```bash
bash scripts/server/launch_multilingual_2026w33.sh --print-only \
  <FULL_COMMIT_SHA> <FROZEN_MANIFEST_JSONL> \
  <VALIDATION_RECEIPT_JSON> <AUDIO_ROOT>
```

The dedicated server Codex task already runs inside the fixed tmux session, so
it must not call the launcher that creates another tmux. After preflight, run
the inner runner directly in the existing session:

```bash
DRONE_W33_MULTILINGUAL_EXECUTION_APPROVED=YES \
bash scripts/server/run_multilingual_2026w33_all.sh \
  <FULL_COMMIT_SHA> <FROZEN_MANIFEST_JSONL> \
  <VALIDATION_RECEIPT_JSON> <AUDIO_ROOT>
```

The inner runner refuses a dirty or mismatched commit.

## Monitoring and handoff

```bash
tmux has-session -t weekly_drone_2026w33_multilingual_es_de
tmux capture-pane -pt weekly_drone_2026w33_multilingual_es_de -S -200
```

For each lane and seed, record start/completion/abort receipts, checkpoint and
config hashes, selection/calibration receipts, metrics, and per-sample
predictions. The server task must send a Management handoff after each phase and
must not modify Notion directly.

## Abort conditions

Stop without starting or continuing training if any of the following occurs:

- archive/version/license/hash mismatch;
- unexpected archive path or unsafe extraction member;
- decode, duration, clipping, NaN, or lineage failure;
- missing class/language/split cell;
- speaker/source-family or duplicate overlap;
- Dataset receipt/manifest/consumer mismatch;
- dirty or incorrect Git SHA;
- missing GPU/conda/runtime capacity;
- existing tmux session with the fixed name;
- output path collision or a prior non-resumable abort receipt.
