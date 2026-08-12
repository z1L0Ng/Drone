# 西班牙语 + 德语三分类 intake 实现准备 v1

- Task: `DATA-20260812-02`
- Date: `2026-08-12` (`America/Chicago`)
- Status: `IMPLEMENTATION READY / METADATA FEASIBILITY ONLY / AUDIO AND TRAINING NO-GO`
- Branch: `codex/multilingual-es-de-dataset-prep`
- Canonical model outputs: exactly `emergency / movement / unknown`
- Hard boundary: source word is provenance and within-class sampling metadata, not a model output

本任务只准备 contract、metadata-only split proposal 工具、validator、synthetic fixtures/tests 和未来 server 命令。未下载、读取或转换音频；未创建真实 canonical split；未训练或评测。

## 1. Evidence labels

- **Verified Source Fact**：仓库现有三类/16 kHz/1 s contract；已固定的 GSC/MSWC version、source revision、license 和 metadata checksum receipt；RAE/Duden 词典条目中确实存在的词义。
- **Audit**：MSWC 同形词在无句子上下文的 force-aligned word clip 中是否表达控制语义；speaker/family leakage 风险；转换是否保持标签。
- **Proposed Policy**：三类 surface mapping、protected policy、unknown admission、speaker+family component split、sampling cap、freeze gate。
- **Not established**：没有真实 native reviewer；Management-provisional engineering admission 不是 native approval 或跨语言语义等价；没有 canonical split、audio receipt、训练或性能结果。

## 2. Frozen surface mapping

### 2.1 Spanish (`es`, MSWC 1.0)

| Role | Frozen candidate surfaces | Status and principal risk |
|---|---|---|
| emergency | `alto` | dictionary-backed Management-provisional positive candidate for phase-1 engineering, **not native-approved**; RAE supports a stop/suspend interjection sense, but the same spelling has extensive high/tall and other senses; isolated MSWC context is unresolved |
| movement | `arriba`, `abajo`, `izquierda`, `derecha`, `adelante`, `atrás`, `sigue` | Management-provisional engineering candidates, **not native-approved**; several are direction/locative/noun/adjective forms rather than guaranteed imperatives; `sigue` may mean continue or follow |
| protected / ambiguous | `para`, `stop`, `sube`, `baja`, `sígueme`, `vamos` | excluded from unknown; `para` is especially ambiguous between stop imperative and preposition; others may be movement/emergency synonyms |
| unknown-candidate | `cero`, `uno`, `dos`, `tres`, `cuatro`, `cinco`, `seis`, `siete`, `ocho`, `nueve` | conservative approved-unknown v0 for phase-1 engineering only; the full inventory complement is excluded |

### 2.2 German (`de`, MSWC 1.0)

| Role | Frozen candidate surfaces | Status and principal risk |
|---|---|---|
| emergency | `halt` | dictionary-backed Management-provisional positive candidate for phase-1 engineering, **not native-approved**; Duden supports the stop imperative/interjection, but also points to the same-spelling particle; isolated MSWC context is unresolved |
| movement | `hoch`, `runter`, `links`, `rechts`, `vorwärts`, `rückwärts`, `folge`, `los` | Management-provisional engineering candidates, **not native-approved**; several are direction/locative forms; `folge` may be noun/imperative; Duden supports a prompt/start-command sense of `los`, but also records other senses and a same-spelling adjective |
| protected / ambiguous | `stopp`, `stop`, `oben`, `aufwärts`, `hinauf`, `rauf`, `unten`, `abwärts`, `hinunter`, `zurück`, `folgen`, `geh`, `gehen` | excluded from unknown because they may express stop, movement, follow, go, or return |
| unknown-candidate | `null`, `eins`, `zwei`, `drei`, `vier`, `fünf`, `sechs`, `sieben`, `acht`, `neun` | conservative approved-unknown v0 for phase-1 engineering only; the full inventory complement is excluded |

### 2.3 Lexical source receipts and limit

- RAE, [`alto`](https://dle.rae.es/alto), accessed `2026-08-12`: the entry includes an interjection used to order someone to stop/suspend an activity, while the same spelling has many adjective, noun, and adverb senses.
- Duden, [`halt`](https://www.duden.de/rechtschreibung/halt_halten_stoppen), accessed `2026-08-12`: the interjection entry gives stop/not-continue meanings and links a same-spelling particle.
- Duden, [`los`](https://www.duden.de/rechtschreibung/los_Aufforderung_locker), accessed `2026-08-12`: the adverb entry includes prompt/start-command use and other senses.

These dictionary facts justify retaining `alto`, `halt`, and `los` as candidates. They do **not** prove the sense of every same-spelling MSWC segment, do not replace source-context review, and do not constitute native approval.

Management permits the frozen candidates to proceed through phase-1 **engineering metadata feasibility**, so missing native review is no longer a hard gate for this stage. It remains a recorded deferred risk and a hard requirement before any paper-level native-semantics or cross-language-equivalence claim.

### 2.4 Conservative approved unknown inventory v0

Artifact: `config/multilingual_three_class/approved_unknown_inventory_v0.csv`

- file SHA-256: `24ac0f8b6536af1645dea604abb5acdf57cb14525a01e509c6c47663c2d0ac02`;
- canonical SHA-256 over sorted `language,surface,train,dev,test`: `b699c0fe9ae8672e67a05da6b76cc3cccfb8f9a1cb4c7de36b40bee11d8d57b5`;
- 20 rows: 10 Spanish and 10 German cardinal-number words;
- Spanish raw support: train `21,762`, dev `2,725`, test `2,725`, total `27,212`; weakest word `cero`, total `1,150`;
- German raw support: train `20,210`, dev `2,531`, test `2,531`, total `25,272`; weakest word `null`, total `299`.

Selection rule: use only cardinal-number surfaces with nonzero support in every pinned source split. Exclude every positive/protected/ambiguous item and every identified direction, stop, start, go, return, or follow synonym/near-synonym. Do not use the full inventory complement. The inventory must be re-reviewed if phase-1 gains numeric-control semantics.

Counts were recovered from `VALID=True` rows in the six pinned MSWC metadata files. The config records their individual SHA-256 receipts. These are pre-global-grouping counts; they are not final train/val/test support.

### 2.5 English anchor

GSC raw v0.02 keeps the current three-class anchor policy:

- emergency: `stop`;
- movement: `up`, `down`, `left`, `right`, `forward`, `backward`, `follow`, `go`;
- spoken unknown allowlist: the other 26 official GSC words recorded in the config;
- `_background_noise_`: protected separate provenance lane, not silently counted as a spoken unknown word.

## 3. Versioned intake contract

Canonical config: `config/multilingual_three_class/es_de_v1.yaml`. It is deliberately JSON-compatible YAML so the validator needs only the Python standard library.

The config freezes:

- dataset ID, version, source revision, official URL, license and provenance;
- exact three output classes and explicit `source_words_are_model_outputs=false`;
- per-language positive, protected, and unknown-candidate rules with review status and semantic risk;
- future mono PCM WAV, 16 kHz, 16-bit, exactly 16,000-sample contract and transform receipts;
- global isolation by both `speaker_id` and `source_clip_family`;
- deterministic 60/20/20 proposal with seed `20260812`;
- equal language/equal class weights, no replacement, five clips per speaker/class/split cap, and smallest-supported-class ceilings;
- no audio download/transform, canonical split, training, or evaluation authorization.

Known immutable receipts in the config include MSWC repository revision `0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218` and the Spanish/German metadata bundle hashes. GSC currently has only the official v0.02 archive ETag/size/date receipt; its archive SHA-256 remains `UNKNOWN_metadata_intake_required`, which validator reports rather than inventing.

## 4. Metadata-only feasibility implementation

### 4.1 Inputs

The CLI accepts only a local config and a checksummed local metadata index. It has no downloader and rejects URL paths.

Supported adapters:

- `mswc_csv`: first-party `LINK,WORD,VALID,SPEAKER,GENDER`; the basename of `LINK` removes the extracted-word directory and recovers the original Common Voice source clip-family; invalid rows are excluded.
- `normalized_csv`: GSC or another pre-audited metadata inventory with `source_record_id,dataset_key,dataset_version,language,source_word,speaker_id,source_clip_family,original_split`.

Every metadata-index entry must include an exact file SHA-256, dataset version, source revision, language and original split. Missing speaker, family, version, revision, file, or checksum fails closed.

The template `config/multilingual_three_class/metadata_index.template.json` is intentionally non-runnable until every absolute path and `REPLACE_WITH_64_HEX_SHA256` value is replaced with a verified receipt.

### 4.2 Global isolation algorithm

For every mapped row, the tool creates a bipartite edge:

```text
dataset-scoped speaker_id <-> dataset-scoped source_clip_family
```

It unions all edges across languages, words, three classes, and original source splits. Each complete connected component—not an individual clip or word—is then assigned once. A deterministic, target-ratio-aware greedy assignment uses the frozen seed and language/class profiles. Therefore any speaker or Common Voice source family connected through another word remains in a single proposed split.

This is a proposal only. The output always states `canonical_split_created=false`; no option can create a canonical split.

### 4.3 Outputs

Default dry-run writes nothing and prints a JSON feasibility report containing:

- config file/canonical hashes and metadata-index hashes;
- every input metadata path/version/revision/SHA receipt;
- virtual `proposal_manifest_sha256` computed without writing a manifest;
- support by language/class/split, source-word counts, speakers, families, and non-admitted rows;
- post-speaker-cap class ceilings and cross-language common ceilings;
- speaker overlap and source-family overlap assertions;
- explicit shortage and NO-GO reasons.

`--write-proposal` is an explicit metadata-only option that writes `metadata_split_proposal.csv` and `feasibility_report.json`. They remain non-canonical receipts and require a separate execution authorization. It never reads audio.

### 4.4 Remaining hard NO-GO reasons

The lexical gate can now proceed under the Management-provisional engineering policy. Feasibility or intake must still remain NO-GO when any of these hard gates fail:

- GSC obtains an exact metadata/archive receipt and reconstructable class/speaker inventory;
- real metadata shows nonzero post-grouping/post-cap support for all three classes in all splits;
- speaker and Common Voice family overlap is not exactly zero;
- an input path/checksum/version/source revision, speaker ID, or family ID is missing;
- Management has not accepted the source-license, audio/header/QC, and cross-source identity policy.

The feasibility report lists missing native review under `deferred_review_risks`, not `no_go_reasons`.

## 5. Validator and synthetic tests

Validator:

```bash
python scripts/validate_multilingual_three_class_intake.py \
  --config config/multilingual_three_class/es_de_v1.yaml
```

Tests:

```bash
python -m unittest -v tests.test_multilingual_three_class_intake
```

Synthetic coverage:

- same speaker across different source words/classes stays in one split;
- different speakers sharing one Common Voice family stay in one split;
- `para` and `stopp` never enter unknown;
- exact three-class schema and source-word-not-output invariant;
- deterministic proposal/support/manifest hash;
- missing identity, duplicate source-record ID, and checksum mismatch fail closed;
- a `complete_split` declaration whose approved-unknown counts disagree with v0 fails closed;
- raw MSWC adapter strips the word directory from `LINK`, groups the same original Common Voice clip across words, and excludes `VALID=False` rows;
- embedded unknown allowlists agree exactly with the checksummed 20-row inventory artifact.

Synthetic outputs are created only inside temporary test directories and are deleted by the test harness. They are not real dataset splits.

### 5.1 Real pinned-metadata dry-run receipt

A write-free dry-run was executed against the six already-pinned MSWC es/de metadata CSVs. It did not include GSC metadata and did not write a proposal:

```bash
python scripts/multilingual_three_class_intake.py \
  --config config/multilingual_three_class/es_de_v1.yaml \
  --metadata-index /tmp/es_de_mswc_real_index.json
```

Observed receipt:

- metadata index file SHA-256: `37cd1285877d87a5277d1ccd1c2eae5a3c42e5463aafb254253020bc8ad6da5f`;
- virtual proposal-manifest SHA-256: `6b894e70c182cdcc11ae1307c6dc98df413dd33a9dbafc30078cc9ace377db40`;
- `58,376` mapped rows in `11,959` speaker/family connected components;
- approved-unknown original-split counts verified exactly for both `es` and `de`;
- lexical engineering gate: `PASS_MANAGEMENT_PROVISIONAL`;
- proposed-split overlap: speaker `0`, source-family `0`;
- post-five-per-speaker/class balance ceilings: Spanish train/val/test `167 / 46 / 70`; German `357 / 112 / 126`;
- English support and common-language ceiling: `0`, because no GSC metadata was supplied;
- final status: `NO_GO`, as expected from the missing English receipt and all downstream authorization/QC gates.

The proposed assignment is an audit calculation over metadata, not a created split. The es/de ceiling values are deterministic under the current config and pinned metadata but remain Proposed Policy outputs, not canonical support.

## 6. Exact future server commands — do not execute under this task

Assumptions for the commands below:

- repository checkout is `/SERVER/PATH/Drone`;
- authorized, already-local metadata exists under `/SERVER/PATH/pinned_metadata`;
- no audio archive is accessed;
- the operator has replaced every template path/checksum and independently reviewed the resulting index.

### Stage S0 — local code/config verification

```bash
cd /SERVER/PATH/Drone
git rev-parse HEAD
git status --short
python -m py_compile src/multilingual_three_class_intake.py scripts/multilingual_three_class_intake.py scripts/validate_multilingual_three_class_intake.py tests/test_multilingual_three_class_intake.py
python -m unittest -v tests.test_multilingual_three_class_intake
python scripts/validate_multilingual_three_class_intake.py --config config/multilingual_three_class/es_de_v1.yaml
shasum -a 256 config/multilingual_three_class/es_de_v1.yaml
```

Expected receipts: checkout commit, clean/scoped status, compile success, test count/pass result, config file hash, canonical config hash, and unresolved receipt list.

### Stage S1 — prepare and verify the local metadata index

```bash
cd /SERVER/PATH/Drone
cp config/multilingual_three_class/metadata_index.template.json /SERVER/PATH/pinned_metadata/es_de_metadata_index.json
shasum -a 256 /SERVER/PATH/pinned_metadata/*.csv
shasum -a 256 /SERVER/PATH/pinned_metadata/es_de_metadata_index.json
```

After `cp`, the operator must replace every placeholder path and SHA-256 using the independently pinned local metadata. The intake command will reject an unedited template, a URL, a checksum mismatch, or a version/revision mismatch.

Expected receipts: per-file SHA-256, index SHA-256, absolute local paths, adapter, dataset/release/source revision, language and original split. A shell glob listing is not itself a manifest; the reviewed JSON index is the receipt.

### Stage S2 — default dry-run, no proposal file

```bash
cd /SERVER/PATH/Drone
mkdir -p /SERVER/PATH/receipts/es_de_three_class_v1
python scripts/multilingual_three_class_intake.py \
  --config config/multilingual_three_class/es_de_v1.yaml \
  --metadata-index /SERVER/PATH/pinned_metadata/es_de_metadata_index.json \
  > /SERVER/PATH/receipts/es_de_three_class_v1/dry_run_report.json
python scripts/validate_multilingual_three_class_intake.py \
  --config config/multilingual_three_class/es_de_v1.yaml \
  --report /SERVER/PATH/receipts/es_de_three_class_v1/dry_run_report.json
shasum -a 256 /SERVER/PATH/receipts/es_de_three_class_v1/dry_run_report.json
```

Expected receipts: dry-run report SHA; `canonical_split_created=false`; config/index/virtual manifest hashes; input receipts; three-class support; per-word/speaker/family counts; post-cap ceilings; overlap counts exactly zero; all shortage/NO-GO reasons.

### Stage S3 — optional non-canonical metadata proposal, separately authorized

```bash
cd /SERVER/PATH/Drone
python scripts/multilingual_three_class_intake.py \
  --config config/multilingual_three_class/es_de_v1.yaml \
  --metadata-index /SERVER/PATH/pinned_metadata/es_de_metadata_index.json \
  --write-proposal \
  --output-dir /SERVER/PATH/receipts/es_de_three_class_v1/proposal
python scripts/validate_multilingual_three_class_intake.py \
  --config config/multilingual_three_class/es_de_v1.yaml \
  --report /SERVER/PATH/receipts/es_de_three_class_v1/proposal/feasibility_report.json
shasum -a 256 /SERVER/PATH/receipts/es_de_three_class_v1/proposal/metadata_split_proposal.csv /SERVER/PATH/receipts/es_de_three_class_v1/proposal/feasibility_report.json
```

Expected receipts: the two output hashes, internal `proposal_manifest_sha256` matching the CSV bytes, zero overlap assertions, and `canonical_split_created=false`. This stage still does not authorize audio download, conversion, canonical split creation, training, or evaluation.

## 7. Future audio download plan only

No download entrypoint is implemented. If Management later authorizes audio intake, a separate task must first freeze:

1. exact official URL and representation (MSWC hosted WAV or publisher Opus, never silently mixed);
2. archive size, release/revision, license text hash and expected SHA-256;
3. quarantine destination and available capacity;
4. downloader/version/retry/resume behavior;
5. post-download archive hash and file inventory;
6. a separate transform authorization with header-level QC and per-output receipts.

Metadata feasibility does not authorize any of those steps.

## 8. Admission gates and decisions still required

1. Obtain and record real Spanish/German native-review decisions before paper-level native-semantics or equivalence claims; engineering provisional admission does not satisfy that claim gate.
2. Review whether the numeric unknown v0 policy remains appropriate if any future command vocabulary includes numeric control.
3. Decide whether `alto`/`halt` sentence-context ambiguity requires context metadata, exclusion rules, or another source; never treat all homographs as commands.
4. Approve MSWC CC BY 4.0 plus no-reidentification terms for the intended use.
5. Approve dataset-scoped identity namespaces and record residual cross-source identity uncertainty.
6. Review real dry-run support and component concentration before authorizing any non-canonical proposal output.
7. Issue separate authorizations for audio download, transform, canonical split, training and evaluation; none is implied here.
