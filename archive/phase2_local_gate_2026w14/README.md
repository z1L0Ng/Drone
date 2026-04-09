# Phase2 Top2 Local Gate Script (Archive, 2026w14)

This folder stores the one-off local evaluation script used for the 2026w14
phase2 strict lexical benchmark gate.

Why archived here:
- It should not be treated as a mainline training/evaluation entrypoint.
- It is preserved for reproducibility of the reported 2026w14 numbers.

Script:
- `run_phase2_top2_local_gate.py`

Reference run:
```bash
python archive/phase2_local_gate_2026w14/run_phase2_top2_local_gate.py
```

Expected outputs:
- `result/weekly_wrapup_2026w14/phase2_top2_local_eval/*`
- `result/weekly_wrapup_2026w14/phase2_top2_local_finetune/*`
