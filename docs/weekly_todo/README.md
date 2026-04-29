# Weekly TODO Structure

## Folder Convention
- Year folder: `docs/weekly_todo/<year>/`
- Week folder: `docs/weekly_todo/<year>/<year>w<week_number>/`
- Required files per week:
  - `todo.md` (required)
  - `runbook.md` (recommended)

## Minimum Requirement for `todo.md`
Each weekly `todo.md` must include:
1. Weekly goals and priorities
2. Execution checklist
3. Branch/model/training changes summary
4. Daily or milestone status log

## Cross-week Log
- Shared handoff log: `docs/weekly_todo/handoff_log.md`

## Workflow Policy
- Weekly Notion page is the source of truth for:
  - weekly TODO planning and assignment
  - pre-meeting weekly report write-up
- `docs/overleaf/` is reserved for paper drafting only (not weekly report drafts).

## Cadence And Project Target
- Weekly planning follows the Thursday noon meeting cadence. The week label
  should follow the planning/meeting cycle, not only the calendar ISO week.
- Current paper target: SenSys 2027 first-round submission.
- Weekly management docs should keep experiment conclusions conservative:
  reproducibility first, deployability second, writing claims only after gates
  are documented.

## Template
- Start from: `docs/weekly_todo/_templates/weekly_todo_template.md`
