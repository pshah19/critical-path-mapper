---
name: critical-path-mapper
description: Compute the critical path, schedule, and cross-team dependency risk for a backlog of tasks with dependencies (e.g. output from the prd-to-jira skill, a Jira export, or any task list with depends_on relationships). Use when the user asks for a critical path, project timeline, schedule, Gantt chart, or wants to know which dependencies/handoffs put a delivery date at risk.
---

# Critical Path & Dependency Risk Mapper

Take a task list with dependencies and turn it into an actual schedule: earliest/latest
start and finish dates per task, slack, the critical path, and every cross-team
handoff that could put the delivery date at risk.

The scheduling math (forward/backward pass, slack, critical path, cross-team edge
detection) is entirely deterministic and lives in
`scripts/critical_path.py`. Your job is everything the script can't do on its own:
normalizing whatever input you're given into the canonical schema below, choosing
reasonable velocity assumptions, and turning the computed output into a plain-language
summary. Never hand-compute a schedule yourself — always run the script.

## When to use this skill

- The user has a backlog (from `prd-to-jira`, a Jira/CSV export, or a plain list) with
  `depends_on` relationships and wants a timeline, critical path, or Gantt chart.
- The user asks "what's blocking what," "where's the schedule risk," or "which team
  handoffs are most likely to slip this."
- Not for producing the backlog itself (see the `prd-to-jira` skill) or for
  summarizing status/progress on work already in flight (that's a status-reporting
  tool, not this one).

## Step 1 — Normalize the input into `tasks.json`

Whatever you're given (an `epics.json` from `prd-to-jira`, a raw Jira CSV export, a
Markdown task list), convert it into this canonical schema. Do not skip fields —
the script has no fallback logic for missing data.

```json
{
  "project": "<short name>",
  "start_date": "YYYY-MM-DD",
  "points_per_day": {
    "default": 2,
    "<team name>": 2.5
  },
  "tasks": [
    {
      "id": "unique-id",
      "summary": "...",
      "team": "<owning team/system — one value, not a list>",
      "story_points": 5,
      "depends_on": ["other-id"],
      "risk": "low"
    }
  ]
}
```

Notes on filling this in:
- `team` is a single owning team per task, not a label list. If the source has
  multiple labels (e.g. `["backend", "finance-reporting"]`), pick the one that best
  represents who actually does the work and is accountable for the handoff — this
  drives the cross-team-blocker detection, so be deliberate rather than defaulting to
  the first label.
- `start_date` should be a real (business) day — if the user doesn't give one, default
  to the next Monday from today and say so explicitly in your summary.
- `points_per_day` is a velocity assumption per team (a "how many story points does
  this team burn per business day" estimate). If the user hasn't told you their
  team's velocity, use `2` as the default and flag in your summary that the schedule
  is built on an assumed, unverified velocity — this is exactly the kind of number a
  TPM should sanity-check before trusting a delivery date, not something to present as
  fact.
- `risk` is optional and only carried through if the source already has it (e.g. from
  `prd-to-jira`'s output) — don't invent it.

## Step 2 — Run the script

```bash
python3 skill/scripts/critical_path.py path/to/tasks.json --outdir path/to/output
```

The script will fail loudly (and tell you exactly which task ids are involved) if:
- any `depends_on` id doesn't resolve to a real task
- the dependency graph has a cycle
- a task references a `team` with no matching `points_per_day` entry and no `default`

Fix `tasks.json` and re-run rather than trying to work around a validation error.

## Step 3 — Outputs

In `--outdir`:
- `schedule.json` — every task's computed duration, earliest/latest start/finish
  dates, slack (business days), and whether it's on the critical path.
- `critical_path.md` — narrative: total project duration and finish date, the
  critical path chain, a "near-critical" watch list (small but nonzero slack), and a
  count of cross-team handoffs on vs. off the critical path.
- `gantt.mmd` — a Mermaid `gantt` chart (grouped into sections by team, critical tasks
  marked `crit`, weekends excluded) built from the computed dates.
- `risk_register.md` — every cross-team dependency edge (the task's `team` differs
  from its dependency's `team`), each flagged critical / near-critical / not on the
  path, plus any `risk` value carried through from the source data.

## Step 4 — Summarize for the user

State plainly: the computed finish date, the velocity assumptions the schedule rests
on (and that they're assumptions, not facts, if you defaulted them), the critical
path in one sentence, and the top 2-3 cross-team handoffs worth watching — prioritize
ones that are on or near the critical path over ones that aren't, since slack absorbs
risk that off-path handoffs pose.
