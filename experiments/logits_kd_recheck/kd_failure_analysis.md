# Logits KD Failure Analysis (pending)

- run_id: `drone_2026w13_local_eval`
- status: pending logits recheck checkpoints from server
- expected: `/Users/zilongzeng/Research/Drone/saved_models/weekly_drone_2026w13/logits_recheck/`
- analysis focus:
  - early-epoch instability
  - soft-target mismatch under low SNR
  - representation transfer stability vs logits transfer
