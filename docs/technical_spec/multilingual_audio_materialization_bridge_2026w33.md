# W33 multilingual audio materialization bridge

Task: `DATA-20260812-03`
Status: implementation and synthetic validation only; no real download, split,
audio conversion, server dispatch, training, or evaluation was performed.

## 1. Frozen boundary

The phase-1 model remains exactly:

```text
emergency / movement / unknown
```

Dataset words remain provenance and within-class sampling fields. They are not
model outputs. Spanish `alto`, German `halt`, and German `los` remain
dictionary-backed, Management-provisional engineering mappings; they are not
native-approved or evidence that every same-spelling source segment has a
command sense. The v0 Spanish/German unknown inventory remains the approved
number-word allowlist zero through nine.

The proposal split contract is now exactly:

| Split | Ratio | Permitted role |
|---|---:|---|
| `train` | 0.60 | optimizer input |
| `validation_selection` | 0.15 | checkpoint selection only |
| `validation_calibration` | 0.10 | post-selection calibration only |
| `test` | 0.15 | sealed final evaluation only |

Seed is `20260812`. Assignment operates on connected components formed by every
dataset-scoped `speaker_id <-> source_clip_family` edge. Speaker, source-family,
isolation-component, and exact decoded-audio duplicate overlap across splits
all fail closed.

## 2. Producer-consumer audit

Verified against accepted Baseline commit
`1a261df80ac12729d0820cb089372c01e39b1c2e`:

- manifest schema: `drone.multilingual_audio_manifest.v0`;
- validation receipt schema:
  `drone.multilingual_manifest_validation_receipt.v0`;
- ordered labels: `emergency`, `movement`, `unknown`;
- manifest languages: `en`, `es`, `de`;
- splits: the four names above;
- receipt: `owner=dataset`, non-empty `validator_version`, `status=pass`,
  `frozen=true`, exact manifest hash, ordered labels, complete languages, and
  isolation/duplicate overlap counts `0/0`;
- audio: PCM WAV, mono, 16 kHz, exactly 16,000 decoded frames, finite values,
  matching file-byte and decoded-float32 hashes.

The dispatch text called the row a “20-field” JSONL. The actual accepted
consumer's `REQUIRED_FIELDS` tuple contains **21 fields**. The producer follows
the executable 21-field contract exactly and writes no lineage-only fields into
the manifest. Raw-to-derived lineage is kept in a separate immutable JSONL.

## 3. Official acquisition plan

Primary-source metadata was rechecked on 2026-08-12. The versioned plan is:

```text
config/multilingual_three_class/server_audio_bridge_v0.json
```

### GSC v2

- official archive:
  `https://storage.googleapis.com/download.tensorflow.org/data/speech_commands_v0.02.tar.gz`;
- release: `raw_v0.02`;
- bytes: `2,428,923,189`;
- SHA-256:
  `af14739ee7dc311471de98f5f9d2c9191b18aedfe957f4a6ff791c709868ff58`;
- ETag: `6b74f3901214cb2c2934e98196829835`;
- last modified: `Wed, 11 Apr 2018 19:41:55 GMT`;
- checksum source: TensorFlow Datasets official
  `tensorflow_datasets/datasets/speech_commands/checksums.tsv`;
- license: CC BY 4.0; attribution receipt required.

### MSWC 1.0

- official first-party repository:
  `https://huggingface.co/datasets/MLCommons/ml_spoken_words`;
- pinned revision:
  `0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218`;
- representation: official WAV/16 kHz shards only;
- Spanish tree: 22 archives, `15,040,133,986` bytes, canonical asset-index
  SHA-256 `a16401e8d93eb4c7047a0edfd5ca2c1c24af24993d29380c13beb33deb5e6c50`;
- German tree: 42 archives, `25,566,926,807` bytes, canonical asset-index
  SHA-256 `cefb7e9a632ccd3d75680507c0ef8f37b8c7d3c276ac57e3fa165c7d4ba74296`;
- official pinned split metadata is acquired as two additional archives:
  Spanish `splits.tar.gz` is `51,330,879` bytes with SHA-256
  `d78b2c6ce54edeb8fa8d2b87b70989cfb98b042925b10fec2879dfb2d27cc6c2`;
  German is `149,381,352` bytes with SHA-256
  `012c26fdb5a2cbaeb1a750ec5c494cbff47c0d47240a5fc8c245fbc879819ae5`;
- each metadata archive must extract exactly `train.csv`, `dev.csv`,
  `test.csv`, and `version.txt`; every file has an independent pinned SHA-256
  in the acquisition plan;
- every resolved archive URL contains the pinned revision; archive bytes are
  checked against the official LFS SHA-256 and size before extraction;
- license: CC BY 4.0 plus the dataset-card condition that users do not attempt
  to determine speaker identities. This bridge performs no re-identification.

The plan preserves attribution and terms receipts and marks redistribution as
unauthorized. It must not be used to publish a source or derived audio bundle
without a separate rights review.

Total expected archive download is `43,236,696,213` bytes (40.27 GiB). The
plan's conservative minimum working-space field is
`108,091,740,532` bytes (100.67 GiB), plus content-addressed derived audio and
receipt space. Derived-audio size is intentionally `UNKNOWN` until the frozen
proposal count and real header probe exist.

## 4. Acquisition and extraction behavior

The server entrypoint is default-dry-run. Real I/O requires both `--execute`
and `DRONE_W33_DATA_DOWNLOAD_APPROVED=YES`.

The runner provides:

- streaming writes to `.part`, HTTP Range resume, and verified reuse;
- URL, response URL, ETag, Last-Modified, Content-Length, byte count, and
  archive SHA receipts;
- pinned Hugging Face tree-index hash/count/byte-total validation before shard
  URLs are accepted;
- safe TAR/ZIP extraction that rejects absolute paths, `..`, links, devices,
  and unexpected tree contents;
- an eight-times compressed-size expansion gate, except that checksum-pinned
  MSWC WAV shards have a stricter absolute declared-size ceiling of
  2,000,000,000 bytes; the member-count and path/type gates still apply;
- extraction into a temporary directory followed by atomic rename;
- expected GSC split-list/word/WAV and MSWC WAV-shard tree validation.

A mismatch never triggers automatic cleanup, redownload, normalization, or
repair of an already verified source. It produces an abort receipt for review.

## 5. Audio materialization contract

Input is an authorized frozen metadata proposal plus a passing acquisition
receipt and acquired source roots. The proposal must include a deterministic
`source_audio_relpath`; zero or multiple matches fail closed.

For every admitted row:

1. verify proposal/config/acquisition receipts and identity isolation;
2. hash the raw source file and bind it to its source archive;
3. decode only WAV PCM and check header/frame/channel parity and finite values;
4. reject empty or full-scale/clipped input;
5. downmix multi-channel input by float64 arithmetic mean and record it;
6. resample with pinned `scipy.signal.resample_poly` only when needed;
7. right-pad short clips with zeros;
8. crop overlength clips only when explicit crop and speech boundaries prove
   the whole admitted word remains inside the one-second window;
9. reject NaN/Inf, clipping, decode, header, and boundary failures;
10. write deterministic PCM16, mono, 16 kHz, exactly 16,000 samples;
11. store by file-byte content address and verify the Baseline decoder;
12. record raw/derived/archive/config/proposal/license lineage.

No normalization, denoising, silence trimming, guessed crop, or zero-file
substitution is performed.

## 6. S0-S3 receipts and resume

Expected root layout:

```text
<W33_DATA_ROOT>/
  archives/
  sources/gsc_v2/raw_v0.02/
  sources/mswc/1.0/metadata/{es,de}/{train,dev,test}.csv
  sources/mswc/1.0/{es,de}/{train,dev,test}/<asset-id>/
  intake/gsc_v2_normalized.csv
  intake/metadata_index.json
  intake/metadata_split_proposal.csv
  intake/feasibility_report.json
  intake/metadata_split_proposal.receipt.json
  materialized/audio/<sha-prefix>/<audio-sha>.wav
  materialized/materialization_index.jsonl
  materialized/audio_lineage.jsonl
  frozen/multilingual_audio_manifest_v0.jsonl
  frozen/multilingual_manifest_validation_receipt_v0.json
  receipts/S1_acquisition.json
  receipts/S1_metadata_bootstrap.json
  receipts/stages/{S0,S1,S2,S3}.json
  receipts/abort.json
```

Stages:

- `S0`: validate only the plan, config, immutable receipts, and real free-space
  gate. It does not require or hash proposal paths;
- `S1`: guarded acquisition and safe extraction; generate complete GSC
  normalized metadata from the official split lists; validate all official
  `VALID` MSWC rows against acquired WAV locators without re-identification;
  emit the checksummed seven-entry metadata index; generate the deterministic
  four-split proposal and Dataset-owned proposal-freeze receipt;
- `S2`: materialize and QC canonical audio plus lineage;
- `S3`: emit/freeze the exact Baseline manifest and Dataset-owner receipt,
  then load it with the accepted Baseline consumer.

A passing stage is reused only when all stage-specific input hashes and every
recorded artifact hash match. S1 records the acquired archives, six official
MSWC CSVs, GSC normalized CSV, metadata index, feasibility report, proposal,
and proposal receipt. Every extracted tree has a deterministic fingerprint over
sorted relative path, file size, and file SHA-256; S2 revalidates all S1 source
trees against those fingerprints before materialization. A mismatched receipt,
archive, tree, or deterministic artifact fails; it is never silently
overwritten. Any exception writes `receipts/abort.json`.

GSC rows are sorted by archive-relative path. `source_record_id` hashes the
dataset, release, relative path, and raw-WAV SHA-256. `speaker_id` is the
filename prefix before `_nohash_`; `source_clip_family` is the exact raw WAV
byte SHA-256, so raw duplicates form one split-isolated component. Official
validation/testing lists are authoritative; train is their archive complement.
Real bootstrap also requires exactly the pinned release inventory count of
`105,829` non-background command WAV rows; the internal `fixture_only` bypass is
test-only and is not exposed by either server CLI.

The six MSWC CSVs remain byte-identical source artifacts. `SPEAKER` is copied
without inference; `LINK` remains the Common Voice clip-family field. Every
official `VALID` row in the frozen three-class target vocabulary must resolve
exactly once to
`WORD_<LINK basename without extension>.wav`, matching the flat official WAV
shard layout. Missing, duplicate, unsafe, or cross-split target locators fail
closed. Other official valid rows remain source evidence but are explicitly
counted as non-target and are not admitted or materialization-audited.

## 7. Exact future server commands (not executed here)

Use explicit paths; do not use shell variables in an audited receipt package.
The placeholders below must be replaced with Management-approved absolute
server paths before execution.

### 7.1 Render the S0-S3 plan without any write/network/audio

```bash
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /ABS/W33
```

No proposal or acquisition receipt must exist. The standalone bootstrap is also
print-only by default:

```bash
python scripts/server/bootstrap_multilingual_metadata_2026w33.py \
  --acquisition-receipt /ABS/W33/receipts/S1_acquisition.json \
  --root /ABS/W33
```

### 7.2 Future authorized execution, one stage at a time

Each command below is currently **HOLD**:

S0 only validates plan/config/space:

```bash
DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /ABS/W33 --stage S0 --execute
```

S1 acquires sources, bootstraps metadata/index/proposal, and freezes the
proposal, so both guards are required:

```bash
DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
DRONE_W33_SPLIT_FREEZE_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /ABS/W33 --stage S1 --execute
```

After independent S1 acceptance, run S2 and S3 separately:

```bash
DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
DRONE_W33_AUDIO_TRANSFORM_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /ABS/W33 --stage S2 --execute

DRONE_W33_DATA_DOWNLOAD_APPROVED=YES \
DRONE_W33_MANIFEST_FREEZE_APPROVED=YES \
python scripts/server/materialize_multilingual_audio_2026w33.py \
  --root /ABS/W33 --stage S3 --execute
```

Do not use `--stage all` for the first real run; review each stage receipt.

### 7.3 Baseline handoff

After S3 and independent Dataset-owner acceptance:

```bash
bash scripts/server/preflight_multilingual_2026w33.sh \
  <40-char-clean-commit> \
  /ABS/W33/frozen/multilingual_audio_manifest_v0.jsonl \
  /ABS/W33/frozen/multilingual_manifest_validation_receipt_v0.json \
  /ABS/W33/materialized/audio
```

Print-only training launch:

```bash
bash scripts/server/launch_multilingual_2026w33.sh --print-only \
  <40-char-clean-commit> \
  /ABS/W33/frozen/multilingual_audio_manifest_v0.jsonl \
  /ABS/W33/frozen/multilingual_manifest_validation_receipt_v0.json \
  /ABS/W33/materialized/audio
```

The manifest, Dataset-owner receipt, and audio root are the exact three inputs
consumed by the Baseline preflight/training wrapper. Their existence does not
authorize training.

## 8. Synthetic evidence and remaining real-data gates

Synthetic fixtures cover all `3 languages x 3 classes x 4 splits` and both GSC
and MSWC path conventions. Tests verify producer-consumer compatibility,
determinism, resampling, stereo downmix, padding, clipping rejection,
overlength boundary rejection, archive/hash/path failures, identity/duplicate
overlap, dual execution guards, and stage resume.

An additional producer-to-intake fixture builds official-shape GSC
`validation_list.txt`/`testing_list.txt` trees plus Spanish/German MSWC
train/dev/test CSV and WAV shard trees. It verifies deterministic GSC record
IDs/locators/speaker groups/raw-byte duplicate families, exact MSWC
`LINK`-to-WAV resolution, a seven-entry checksummed metadata index accepted by
the existing intake loader, default no-write behavior, and hash-verified resume.

A metadata-only dry-run was also repeated against the six previously pinned
MSWC Spanish/German CSVs. It opened no audio and wrote no proposal:

- metadata-index SHA-256:
  `37cd1285877d87a5277d1ccd1c2eae5a3c42e5463aafb254253020bc8ad6da5f`;
- virtual four-split proposal SHA-256:
  `a72b5f6db1ffc3450534f5306de6560599ea45bba42e1d334234bdc0413f89be`;
- 58,376 mapped rows and 11,959 speaker/family connected components;
- speaker overlap `0`; source-family overlap `0`;
- lexical engineering gate: `PASS_MANAGEMENT_PROVISIONAL`;
- post-five-per-speaker/class balance ceilings:

| Language | train | validation_selection | validation_calibration | test |
|---|---:|---:|---:|---:|
| Spanish MSWC | 162 | 57 | 32 | 32 |
| German MSWC | 356 | 97 | 57 | 85 |
| English GSC | 0 | 0 | 0 | 0 |

That earlier result is correctly `NO_GO`: it intentionally contains no GSC metadata,
and all real audio/download/transform/freeze/training gates remain closed. The
figures are deterministic metadata proposal ceilings, not canonical support.

Remaining real-data gates:

- successful real S1 generation and independent review of the full GSC/MSWC
  metadata index and all locator/count receipts;
- recomputed four-split real support after speaker/family connected components;
- explicit metadata proposal freeze authorization;
- server free-space and filesystem receipt;
- real HTTP/archive/tree receipts;
- real audio header, boundary, clipping, duplicate, and conversion QC;
- independent Dataset-owner acceptance of S3;
- separate Baseline server/training authorization.

No performance, dataset-selection superiority, native semantic equivalence,
canonical real split, or E3 claim follows from this bridge.
