# This Week TODO (CDT, Week of 2026-03-30)

## Weekly Goal (Drone)
- Rebuild weekly focus from a clean archive state.
- Define this week’s model/training plan and execution order.
- Keep server/local handoff records strict and minimal.

## Hard Constraints
- Training: server (full dataset).
- Coding/evaluation/plotting/reporting: local.
- Every handoff must be logged in `docs/weekly_todo/handoff_log.md`.

## Daily Execution Checklist
- [ ] `git status` clean/controlled before each handoff.
- [ ] Update this TODO with progress and blockers.
- [ ] Append one row in `docs/weekly_todo/handoff_log.md` with command + outputs + next action.

## Branch / Model / Training Changes (This Week)
| Date | Branch | Type | Change | Paths | Status |
|---|---|---|---|---|---|
| 2026-04-02 | `main` | repo hygiene | Full archive cleanup and week reset to `2026w14` | `archive/`, `docs/weekly_todo/2026/2026w14/` | done |

## Priority Items
### Priority 1 — Define this week experiments
- [ ] Finalize model variants to run this week.
- [ ] Finalize training schedule (server) and evaluation schedule (local).

### Priority 2 — Execute server training
- [ ] Run baseline training for `drone_2026w14`.
- [ ] Record run command and log file in handoff log.

### Priority 3 — Local evaluation and reporting
- [ ] Run local evaluation on completed checkpoints.
- [ ] Export summary tables and weekly report.

## Status Log
- 2026-04-02:
  - Done: archived previous-week assets and reset weekly docs to `2026w14`.
  - Next: fill concrete training/eval tasks for this week and start first server run.
