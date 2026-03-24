# Next-Round Data Collection Protocol (Drone)

## Objective
Collect balanced, high-quality emergency/movement/unknown speech for noisy drone intent recognition.

## Classes and Targets
See `data_collection_plan/target_counts.csv`.

## Recording Matrix
- speaking style: `normal`, `shouted`
- noise condition: `clean`, `drone_noise`
- distance (if available): `near (~1m)`, `mid (~3m)`
- language tag: `en`, `zh`, `ja(optional)`

## Technical Standard
- sample rate: 16 kHz
- channel: mono
- clip length: 1.0 second (trim/pad)
- format: wav

## File Naming
`<speaker>_<lang>_<class>_<style>_<noise>_<distance>_<idx>.wav`

## Quality Acceptance
- audible speech present (no silent/no-voice clips)
- RMS energy above minimum threshold (project script default)
- no clipping or severe distortion
- label matches spoken content

## Metadata Required
- filename
- speaker_id
- language
- class
- style
- noise_condition
- distance
- duration_sec
- rms_energy
- keep/drop
