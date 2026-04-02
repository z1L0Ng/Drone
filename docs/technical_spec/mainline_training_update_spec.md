# Mainline Model/Training Update Spec

## Purpose
This spec defines the required process for any mainline (`main`) model/training update.

## Required Inputs Before Starting
1. Current week TODO exists at `docs/weekly_todo/<year>/<year>w<week>/todo.md`
2. Handoff log is active at `docs/weekly_todo/handoff_log.md`
3. Weekly runbook exists at `docs/weekly_todo/<year>/<year>w<week>/runbook.md` (recommended)

## Required Update Workflow
1. Update weekly TODO
   - Add task intent, scope, and owner in weekly `todo.md`
   - Add or update one row in `Branch / Model / Training Changes`
2. Implement and train
   - Keep code/data/training changes scoped and traceable
   - Save outputs to deterministic directories with weekly tag
3. Evaluate and summarize
   - Export core metrics and a short summary markdown
   - Mark incomplete runs explicitly (do not silently drop)
4. Handoff logging
   - Append one row to `docs/weekly_todo/handoff_log.md`
   - Include command, output path, next owner/action, and risk

## Required Artifact Checklist
- Training config snapshot
- Model checkpoint path (or pointer)
- Evaluation metrics file
- Summary markdown with interpretation
- Weekly TODO and handoff log updates

## Naming and Traceability Rules
- Use weekly tag format: `drone_<year>w<week>` (example: `drone_2026w13`)
- Result/model directories should include weekly tag
- Each summary must reference command and output directories

## Merge Gate for Mainline
Mainline updates should not be considered complete unless:
1. Weekly TODO is updated
2. Branch/model/training changes table is updated
3. Handoff log row is added
4. Required artifacts are present or explicitly marked pending
