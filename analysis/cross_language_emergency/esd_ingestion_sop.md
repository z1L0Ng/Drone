# ESD Ingestion SOP (Phase1.2+)

## Objective
Place licensed ESD audio into the isolated phase1 root without touching repo-tracked dataset folders.

## Fixed Target Path
- ESD root: `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd`
- Do NOT place under:
  - `/Users/zilongzeng/Research/Drone/dataset/`
  - `/Users/zilongzeng/Research/Drone/local_data/cross_language/`

## Required Folder Convention
- Keep files under any nested structure, but directory/file names should contain emotion tokens when possible:
  - `ang` / `anger`
  - `neu` / `neutral`
  - `sur` / `surprise` (optional)
  - `fear` (if available)
- Supported audio formats for scanner: `.wav`, `.flac`, `.mp3`, `.m4a`, `.ogg`

## Ingestion Steps
1. Obtain ESD package via licensed channel (manual download by authorized user).
2. Verify package checksum or provider integrity note.
3. Extract/copy all audio to `/tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd`.
4. Quick sanity check:
   - `find /tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd -type f | wc -l`
   - `find /tmp/drone_acoustic_2026w14_phase1_downloads/raw/esd -type f \( -iname '*.wav' -o -iname '*.flac' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.ogg' \) | wc -l`
5. Do not commit raw audio into git.

## Acceptance Criteria
- ESD isolated root contains readable audio files.
- `sample_count_table_2026w14.csv` scanned rows for ESD become non-zero after rescan.
