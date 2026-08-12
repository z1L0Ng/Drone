# W33 English + Spanish + German clean-slate retraining preparation

## Status and evidence boundary

Task: `BASE-20260812-03`.

This is an implementation-preparation artifact. Local validation is restricted
to generated synthetic one-second tones. It contains no downloaded audio, real
training, real evaluation, server execution, leaderboard, or paper-facing
result.

The primary output contract is one shared encoder in this exact order:

```text
0 emergency
1 movement
2 unknown
```

Language and source word are provenance and sampling fields only. They are not
model inputs or output heads. The three primary comparison lanes use the same
frontend, model profile, fresh-random initialization rule, seed IDs, training
budget, checkpoint selection rule, calibration rule, shared EN/ES/DE test
manifest, and metric schema.

Source differences cannot be interpreted as language effects: English comes
from GSC v2 while Spanish and German come from MSWC. The pooled lanes therefore
measure a pooled-source training recipe under this manifest, not a causal
language effect.

## Legacy entrypoint exclusion

`src/data_pre.py` scans directories, downsamples classes, and performs seeded
file-level `train_test_split`. The W33 entrypoint never imports or reads its
`data_paths.npz` output. It accepts only:

1. a versioned JSONL manifest;
2. a Dataset-owner validation receipt with `status=pass` and `frozen=true`;
3. an exact manifest SHA-256 match;
4. zero attested isolation/duplicate overlap;
5. the four preassigned splits `train`, `validation_selection`,
   `validation_calibration`, and `test`.

The consumer rechecks schema, paths, audio metadata, unique sample IDs,
speaker/voice isolation groups, duplicate groups, language/source mapping, and
the receipt hash. It never creates a split.

## Dataset-owner manifest adapter contract

Schema IDs:

- JSONL row: `drone.multilingual_audio_manifest.v0`
- validation receipt: `drone.multilingual_manifest_validation_receipt.v0`

Every JSONL row must provide:

```text
schema_version, manifest_version, sample_id, relative_audio_path,
audio_sha256, decoded_pcm_sha256, source_dataset, source_release,
language, source_word, label, speaker_id, voice_id, isolation_group_id,
duplicate_group_id, split, license_id, provenance_status,
sample_rate_hz, channels, num_samples
```

Accepted real source IDs in v0 are `gsc_v2` for English and `mswc` for
Spanish/German. If the Dataset owner uses different identifiers, Management
must approve and update the versioned source mapping rather than relying on a
runtime alias.

The validation receipt must identify `owner=dataset` and a validator version,
and contain the manifest hash, schema, ordered labels, languages, `frozen=true`,
`status=pass`, and zero counts for isolation-group and duplicate-group
cross-split overlap. The consumer accepts one full EN/ES/DE
manifest and derives the EN-only view by language filtering; its split remains
the Dataset-owner split.

Support is always derived from the accepted manifest. No support number is
hard-coded in configs or code.

## Audited and frozen project frontend contract

The audit source is the current project pair `src/model_config.py` and
`src/logmel_frontend_shared.py`. They declare:

- 16 kHz and one second;
- `n_fft=1024`, `hop_length=512`, `center=false`;
- 256 mel bins, `fmin=50 Hz`, `fmax=None`, power `2.0`;
- per-example `power_to_db(ref=max, top_db=80)`;
- `MAX_FRAMES=32` and model input `(256, 32, 1)`.

W33 freezes that current-project contract as
`current_project_logmel_256x32_v0`. With a 16,000-sample signal, the non-centered
STFT produces 30 frames; the current project contract right-pads the feature to
32 frames with `0.0 dB`. No dataset mean/std normalization is added.

The new loader makes the waveform boundary stricter: input must already decode
as mono, 16 kHz, and exactly 16,000 samples. It rejects rather than silently
resampling, cropping, padding, substituting zeros, or mixing channels. It
checks both file bytes and decoded little-endian float32 PCM hashes. The
feature tensor is also hashed as contiguous little-endian float32.

Config and implementation hashes are written to every start/completion/abort
receipt. A future frontend change requires a new contract/config version and
cannot share the main comparison table.

## Versioned lanes

| Lane | Config | Sampling | Interpretation |
|---|---|---|---|
| EN-only anchor | `config/multilingual_2026w33/en_only_anchor_v0.json` | Uniform English train/selection/calibration; one shared EN/ES/DE test pass | Cross-source transfer anchor, not a causal language-effect estimate |
| Naive pooled diagnostic | `config/multilingual_2026w33/multilingual_naive_pooled_v0.json` | Uniform examples across the pooled manifest | Diagnostic exposure to source imbalance |
| Balanced main | `config/multilingual_2026w33/multilingual_balanced_main_v0.json` | Equal language/class cells, then cyclic word and speaker/voice selection | Main sampling-controlled pooled-source lane |

The balanced sampler is deterministic for a seed, samples language/class cells
equally, and balances source word and speaker/voice within each cell. Sampling
may repeat records when a cell exhausts; the receipt preserves the realized
order. `source_word`, speaker, and language never enter the feature/model tuple.

All primary lanes build `src.model:build_model` with the same `base` profile,
one `(256,32,1)` input, and one 3-class softmax. Initialization is always fresh
random and `checkpoint_input` must be null. No old checkpoint or result is read.

Teacher/student is intentionally absent from the primary configs. It may be
introduced only as a separately named recipe after a clean teacher completes;
it cannot replace or select the clean-slate primary comparison.

## Training, selection, calibration, and evaluation

Shared seed IDs are `0,1,2`. Component seeds are namespaced hashes of protocol,
lane, seed ID, and component. Shared budget is 50 maximum epochs, batch size 32,
Adam at `1e-4`, and categorical cross-entropy.

Checkpoint selection uses `validation_selection` only. EN-only uses only its
English selection/calibration rows; pooled lanes use EN/ES/DE rows. This keeps
Spanish/German target supervision out of the EN-only anchor. Every lane then
evaluates once on the same frozen EN/ES/DE test rows.

The shared selection rule is:

1. maximum macro-F1;
2. tie: higher emergency recall;
3. tie: lower NLL;
4. tie: earlier epoch.

Early-stopping patience is 10 epochs. After checkpoint selection, scalar
temperature is fit by validation NLL on the disjoint
`validation_calibration` split. The v0 action policy is calibrated argmax with
no tuned threshold. Test bytes are first opened only after checkpoint and
calibration receipts exist, and temperature is never refit on test.

The guarded runner persists:

- `run_config.json`, `start_receipt.json`, `completion_receipt.json`, or
  `abort_receipt.json`;
- selected checkpoint and per-epoch selection history;
- validation-only calibration receipt;
- per-sample predictions with source/language/word, probabilities, confidence,
  audio/PCM/feature/frontend/noise/checkpoint/calibration hashes;
- per-language/class support and recall, per-class precision/recall/F1,
  aggregate macro-F1, emergency and unknown recall, false-emergency and
  unknown-false-emergency rates, NLL, Brier, ECE, and reliability rows.

All real outputs are forced under:

```text
weeklyresult/weekly_drone_2026w33/<run_name>/seed_<ID>/
```

The clean primary noise contract is explicitly disabled and hashed; numeric SNR
levels are null. This does not approve a noisy lane. A later noise manifest and
SNR policy require a new scoped decision/config.

## Local synthetic validation

Unit and integration tests generate minimal mono 16 kHz, one-second WAV tones
inside a temporary directory. They do not read or download real project audio.

```bash
conda run -n drone python -m unittest discover \
  -s tests/multilingual_retraining -p 'test_*.py' -v
```

The CLI dry-run additionally requires `fixture_only=true` in the Dataset-owner
validation receipt, so it cannot be pointed at a real manifest by accident:

```bash
conda run -n drone python scripts/run_multilingual_retraining_2026w33.py \
  --mode dry-run \
  --config config/multilingual_2026w33/multilingual_balanced_main_v0.json \
  --manifest /tmp/<fixture>/manifest.jsonl \
  --manifest-validation-receipt /tmp/<fixture>/manifest_validation_receipt.json \
  --audio-root /tmp/<fixture>/audio \
  --output-dir /tmp/<fixture>/dry_run_output
```

## Prepared server preflight and launch

No command in this section was dispatched by `BASE-20260812-03`.

Run preflight at the exact committed SHA. It verifies development audio and
does not open sealed-test bytes:

```bash
bash scripts/server/preflight_multilingual_2026w33.sh \
  <40-char-commit> <frozen-manifest.jsonl> \
  <manifest-validation-receipt.json> <audio-root>
```

Render the tmux launch without creating a session:

```bash
bash scripts/server/launch_multilingual_2026w33.sh --print-only \
  <40-char-commit> <frozen-manifest.jsonl> \
  <manifest-validation-receipt.json> <audio-root>
```

The prepared session name is:

```text
weekly_drone_2026w33_multilingual_es_de
```

Actual launch has two independent guards: `--execute` plus
`DRONE_W33_SERVER_DISPATCH_APPROVED=YES`. The inner runner also requires
`DRONE_W33_MULTILINGUAL_EXECUTION_APPROVED=YES`, the exact clean Git SHA, and
validated manifest/audio hashes. A new explicit Management task is required
before setting either guard or creating the tmux session.

## Open blockers and next authorization gate

- Dataset-owner frozen real manifest and passing validation receipt do not yet
  exist in this branch.
- Real GSC v2/MSWC files were not inspected or downloaded.
- Server environment, capacity, paths, and audio hashes were not checked.
- No primary lane has started, so no checkpoint, metric, support, calibration,
  or empirical comparison exists.
- Because source and language are confounded, even a completed pooled-source
  comparison cannot by itself establish a causal language effect.

Next gate: Management reviews the commit and adapter contract, then coordinates
the Dataset-owner manifest handoff. Only a later explicit task may run server
preflight, create the tmux session, or train.
