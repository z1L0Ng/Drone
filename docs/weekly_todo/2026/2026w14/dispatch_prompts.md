# 2026w14 Dispatch Prompts

Use these prompts as-is when assigning work to execution agents.

## Prompt A: Acoustic Agent
```text
You are the acoustic-analysis execution agent for 2026w14.
Scope: dataset scouting and acoustic feature analysis only.

Repository root:
/Users/zilongzeng/Research/Drone

Objectives:
1) First submit dataset options and sample-size estimates for emergency/normal/multilingual validation.
2) Do not start full feature analysis until PI selects dataset option.

Phase-1 required outputs:
- analysis/cross_language_emergency/dataset_options_2026w14.md
- analysis/cross_language_emergency/dataset_manifest_2026w14.csv

After PI selection, Phase-2 required outputs:
- analysis/cross_language_emergency/alpha_ratio.png
- analysis/cross_language_emergency/spectral_centroid_bandwidth.png
- analysis/cross_language_emergency/energy_distribution.png
- analysis/cross_language_emergency/pitch_energy_envelope.png
- analysis/cross_language_emergency/findings.md
- analysis/cross_language_emergency/summary_2026w14.md

Do not edit:
- docs/weekly_todo/*
- TODO_THIS_WEEK.md
- docs/technical_spec/*
```

## Prompt A2: Acoustic Agent (Phase2 Gate + Multilingual Expansion)
```text
You are the acoustic-analysis execution agent for 2026w14.
Keep working on branch: codex/acoustic-2026w14-phase1.

Policy lock:
1) English gate first:
   - validate emergency vs normal separability in English phase1 package.
2) If gate holds, expand to multilingual next:
   - not limited to Chinese/Japanese; French and others are allowed.
   - only use open datasets with sufficient sample size.
   - label semantics must be mappable to the same English reference:
     emergency vs normal.

Immediate tasks:
1) Re-run ingest/rescan only when ESD scanned audio > 0.
2) Update phase1 artifacts and keep evidence table/onepager current.
3) Submit a multilingual candidate matrix with:
   - language
   - dataset/license
   - emergency/normal mapping compatibility
   - usable sample estimate
   - known risks

Suggested command skeleton (run only when data is ready):
- switch branch: `git switch codex/acoustic-2026w14-phase1`
- set roots: `ESD_ROOT`, `CREMA_ROOT`, `OUT_DIR=analysis/cross_language_emergency`
- gate check: `ESD_AUDIO_COUNT > 0`
- run:
  - `python3 scripts/build_dataset_manifest_2026w14.py ...`
  - `python3 scripts/render_dataset_options_2026w14.py ...`
  - `python3 scripts/analyze_phase1_cremad_acoustics.py ...`
  - refresh `meeting_evidence_table_2026w14.(md/csv)` and `onepager_2026w14_phase1.md`

Do not edit:
- docs/weekly_todo/*
- TODO_THIS_WEEK.md
- docs/technical_spec/*
```

## Prompt B: Model Agent
```text
You are the model/config execution agent for 2026w14.
Scope: prepare and validate command/config package for preprocess_ext and branch_trial.

Repository root:
/Users/zilongzeng/Research/Drone

Required outputs:
1) runnable command pack for both runs
2) concise config delta vs baseline
3) risk note and fallback recommendation
4) expected output paths for model/result/log

Do not edit:
- docs/weekly_todo/*
- TODO_THIS_WEEK.md
- docs/technical_spec/*
- Notion checklist pages
```

## Prompt C: Server Operator
```text
Execute training only for 2026w14 and return receipts in strict format.

Run order:
1) preprocess_ext
2) branch_trial

Must force:
WEEKLY_TAG=drone_2026w14

Required path pattern:
- saved_models/weekly_drone_2026w14/{preprocess_ext,branch_trial}/
- result/weekly_drone_2026w14/{preprocess_ext,branch_trial}/
- logs/weekly_drone_2026w14_{task}_*.log

Startup receipt (within 10 min per run):
- PID
- LOG path
- first 30 log lines

Completion receipt:
- checkpoint path
- result tree
- last 50 log lines
```

## Prompt A3: Acoustic Agent (Post-Meeting Phase2 Multilingual Launch)
```text
You are the acoustic-analysis execution agent for post-meeting phase2.
Keep working on branch: codex/acoustic-2026w14-phase1.

Scope:
- acoustic/dataset analysis only
- no model architecture edits
- no training orchestration edits

Locked policy:
1) English gate already passed in phase1; keep English mapping as reference.
2) Expand multilingual beyond Chinese/Japanese when open datasets are sufficient.
3) Enforce semantic comparability contract:
   - emergency vs normal mapping must be explicitly documented per language.
4) Priority order for immediate execution:
   - Tier-1: Italian, German
   - Tier-2: French

Mandatory inputs to follow:
- analysis/cross_language_emergency/multilingual_priority_scorecard_2026w14.md
- analysis/cross_language_emergency/multilingual_mapping_contract_2026w14.md

Required outputs (first batch):
1) analysis/cross_language_emergency/phase2_multilingual_plan_2026w14.md
2) analysis/cross_language_emergency/phase2_multilingual_dataset_manifest_2026w14.csv
3) analysis/cross_language_emergency/phase2_mapping_audit_2026w14.md

Required fields per language row:
- language
- dataset_name
- license
- source_url
- emergency_labels
- normal_labels
- semantic_match_level (strict/partial)
- usable_sample_estimate
- risks
- recommendation (go/hold)

Execution note:
- If Tier-1 language has no strict mapping or insufficient sample size, mark `hold` and move to next language.
- Do not fabricate counts; separate estimated vs scanned.

Do not edit:
- docs/weekly_todo/*
- TODO_THIS_WEEK.md
- docs/technical_spec/*
```

## Prompt A4: Acoustic Agent (Lexical Inventory + Cross-Lingual Word-Level Alignment)
```text
You are the acoustic-analysis execution agent for phase2 lexical alignment.
Keep working on branch: codex/acoustic-2026w14-phase1.

Goal:
- Make explicit which words/utterances are actually used as analysis corpus, not only language-level labels.
- Separate emotion-label mapping from lexical-content comparability.

Inputs:
- analysis/cross_language_emergency/phase2_multilingual_dataset_manifest_2026w14.csv
- analysis/cross_language_emergency/phase2_mapping_audit_2026w14.md
- analysis/cross_language_emergency/multilingual_mapping_contract_2026w14.md

Required outputs:
1) analysis/cross_language_emergency/phase2_lexical_inventory_2026w14.csv
2) analysis/cross_language_emergency/phase2_lexical_alignment_2026w14.md
3) analysis/cross_language_emergency/phase2_lexical_coverage_summary_2026w14.md

CSV required columns:
- language
- dataset_name
- sample_id
- split_source (estimated/scanned)
- emotion_label_raw
- canonical_label (emergency/normal/excluded)
- raw_utterance_text
- normalized_utterance_text
- english_gloss
- lexical_domain_tag (command/help-call/status/other)
- lexical_comparability (strict/partial/none)
- notes

Execution rules:
1) If dataset has no utterance text/transcript, set `raw_utterance_text=NA` and `lexical_comparability=none`.
2) Do not fabricate text. If only template sentence IDs are provided, keep IDs and mark text availability explicitly.
3) For strict lexical comparability, require semantically matched gloss clusters between English and target language.
4) Keep emotion mapping contract unchanged:
   - mainline: emergency=anger+fear; normal=neutral(+calm)
   - `surprise` remains sensitivity-only

Markdown deliverable expectations:
- `phase2_lexical_alignment_2026w14.md`:
  - per-language lexical availability status
  - top comparable gloss clusters (if any)
  - mismatch reasons
- `phase2_lexical_coverage_summary_2026w14.md`:
  - counts of rows with/without usable text per language
  - recommendation: can lexical-level comparison be claimed in meeting? (yes/no + reason)

Do not edit:
- docs/weekly_todo/*
- TODO_THIS_WEEK.md
- docs/technical_spec/*
```
