# Phase2 Transcript Access Plan 2026W14

## Objective
Unblock lexical-first expansion by prioritizing multilingual datasets with usable utterance text/transcript while preserving canonical mapping:
- emergency = anger + fear
- normal = neutral (+ calm)
- surprise = sensitivity-only

## Evidence Base
- audEERING dataset index shows transcript/text-bearing schemes for target datasets:
  - `emodb`: includes `transcription`
  - `emozionalmente`: includes `transcription`
  - `nemo`: includes `normalized_text` and `raw_text`
  - `quechua`: includes `transcription` and `translation`
- Existing phase2 lexical files show current blocker is transcript/text not staged locally.

## Access Modes By Dataset
| dataset | language | transcript field type | access mode | immediate action |
|---|---|---|---|---|
| `quechua` | Quechua | verbatim (`transcription`, `translation`) | direct_download | pull metadata tables first, then filter anger/fear/neutral |
| `nemo` | Polish | verbatim (`raw_text`, `normalized_text`) | direct_download | pull metadata tables first, build lexical domain tags |
| `emozionalmente` | Italian | template id (`transcription=s0..`) | direct_download | pull sentence index mapping for s* ids before lexical clustering |
| `emodb` | German | template id (`transcription=a01..`) | direct_download | pull label/code mapping (`a01..`) to sentence text for lexical alignment |
| `CaFE` | French | template id (sentence number in file naming) | external_download | fetch sentence inventory from dataset docs/companion paper and bind to file ids |
| `ESD` | Chinese | template sentence set | manual_request | complete research-use license request; then ingest sentence list |

## Unblock Sequence (Lexical-First)
1. Stage transcript metadata for `quechua` and `nemo` (verbatim-first path).
2. In parallel, stage template-id maps for `emozionalmente` and `emodb`.
3. Keep `CaFE` as external-download backup if Tier-1 staging is delayed.
4. Keep `ESD` blocked until license/manual access is approved.

## Go/Hold Rule Applied
- `go`: transcript available + lexical readiness >= partial.
- `hold`: transcript unavailable, or semantic mapping partial, or access still license-gated.

## Minimal Implementation Commands (not executed)
```bash
# Quechua / NEMO transcript metadata pull (example via audb)
python3 - <<'PY'
import audb
# db = audb.load("quechua", version="1.0.2", media=False)
# db = audb.load("nemo", version="1.0.1", media=False)
PY
```

## Risk Notes
- Template-id datasets (`emodb`, `emozionalmente`, `CaFE`) require an additional sentence-map step before strict lexical cluster matching.
- `nemo` and `CaFE` are CC-BY-NC-SA; suitable for research but higher license risk than CC-BY/CC0.
