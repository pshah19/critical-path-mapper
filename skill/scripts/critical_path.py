#!/usr/bin/env python3
"""Compute a critical-path schedule from a canonical tasks.json.

Usage:
    python3 critical_path.py path/to/tasks.json --outdir path/to/output \
        [--near-critical-threshold 3]

Produces, in --outdir:
    schedule.json       - per-task computed schedule (dates, slack, is_critical)
    critical_path.md    - narrative: finish date, critical path chain(s), watch list
    gantt.mmd            - Mermaid gantt chart grouped by team, critical tasks marked
    risk_register.md    - every cross-team dependency edge, flagged by schedule risk

This script is a pure, deterministic critical-path-method (CPM) engine. It does not
infer teams, velocities, or task breakdowns - that normalization happens upstream,
done by the model following skill/SKILL.md, and is captured in tasks.json before this
script runs.
"""

import argparse
import json
import math
import sys
from collections import defaultdict, deque
from datetime import date, timedelta
from pathlib import Path

DEFAULT_NEAR_CRITICAL_THRESHOLD = 3


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def roll_to_business_day(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def add_business_days(base: date, n: int) -> date:
    d = base
    added = 0
    while added < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d


def load_and_validate(path: Path) -> dict:
    data = json.loads(path.read_text())
    tasks = data.get("tasks", [])
    by_id = {t["id"]: t for t in tasks}

    errors = []
    if len(by_id) != len(tasks):
        errors.append("duplicate task ids found")

    for t in tasks:
        for dep in t.get("depends_on", []):
            if dep not in by_id:
                errors.append(f"{t['id']} depends_on unknown id '{dep}'")

    rates = data.get("points_per_day", {})
    for t in tasks:
        if t.get("team") not in rates and "default" not in rates:
            errors.append(
                f"{t['id']}: no points_per_day entry for team '{t.get('team')}' "
                f"and no 'default' rate defined"
            )

    if errors:
        raise ValueError("tasks.json failed validation:\n  " + "\n  ".join(errors))

    return data


def topological_order(by_id: dict) -> list:
    indegree = {tid: 0 for tid in by_id}
    dependents = defaultdict(list)
    for t in by_id.values():
        for dep in t.get("depends_on", []):
            dependents[dep].append(t["id"])
            indegree[t["id"]] += 1

    queue = deque(sorted(tid for tid, d in indegree.items() if d == 0))
    order = []
    indegree = dict(indegree)
    while queue:
        tid = queue.popleft()
        order.append(tid)
        for nxt in sorted(dependents[tid]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(by_id):
        remaining = sorted(set(by_id) - set(order))
        raise ValueError(
            "tasks.json has a dependency cycle involving: " + ", ".join(remaining)
        )
    return order


def compute_schedule(data: dict) -> dict:
    tasks = data["tasks"]
    by_id = {t["id"]: t for t in tasks}
    rates = data.get("points_per_day", {})
    start_date = roll_to_business_day(parse_date(data["start_date"]))

    order = topological_order(by_id)

    duration = {}
    for tid, t in by_id.items():
        rate = rates.get(t["team"], rates.get("default"))
        duration[tid] = max(1, math.ceil(t["story_points"] / rate))

    dependents = defaultdict(list)
    for t in tasks:
        for dep in t.get("depends_on", []):
            dependents[dep].append(t["id"])

    earliest_start = {}
    earliest_finish = {}
    for tid in order:
        deps = by_id[tid].get("depends_on", [])
        earliest_start[tid] = max((earliest_finish[d] for d in deps), default=0)
        earliest_finish[tid] = earliest_start[tid] + duration[tid]

    project_duration = max(earliest_finish.values())

    latest_finish = {}
    latest_start = {}
    for tid in reversed(order):
        succs = dependents[tid]
        latest_finish[tid] = (
            min(latest_start[s] for s in succs) if succs else project_duration
        )
        latest_start[tid] = latest_finish[tid] - duration[tid]

    slack = {tid: latest_start[tid] - earliest_start[tid] for tid in by_id}
    is_critical = {tid: slack[tid] == 0 for tid in by_id}

    return {
        "by_id": by_id,
        "order": order,
        "dependents": dependents,
        "start_date": start_date,
        "duration": duration,
        "earliest_start": earliest_start,
        "earliest_finish": earliest_finish,
        "latest_start": latest_start,
        "latest_finish": latest_finish,
        "slack": slack,
        "is_critical": is_critical,
        "project_duration": project_duration,
        "rates": rates,
    }


def critical_path_chains(sched: dict) -> list:
    by_id = sched["by_id"]
    dependents = sched["dependents"]
    earliest_start = sched["earliest_start"]
    earliest_finish = sched["earliest_finish"]
    is_critical = sched["is_critical"]
    project_duration = sched["project_duration"]

    sinks = [tid for tid in by_id if not dependents[tid]]
    critical_sinks = sorted(
        tid for tid in sinks if earliest_finish[tid] == project_duration
    )

    chains = []
    for sink in critical_sinks:
        chain = [sink]
        current = sink
        while True:
            deps = by_id[current].get("depends_on", [])
            candidates = sorted(
                d
                for d in deps
                if is_critical[d] and earliest_finish[d] == earliest_start[current]
            )
            if not candidates:
                break
            current = candidates[0]
            chain.append(current)
        chains.append(list(reversed(chain)))
    return chains


def cross_team_edges(sched: dict) -> list:
    by_id = sched["by_id"]
    is_critical = sched["is_critical"]
    earliest_start = sched["earliest_start"]
    earliest_finish = sched["earliest_finish"]
    slack = sched["slack"]

    edges = []
    for tid, t in by_id.items():
        for dep in t.get("depends_on", []):
            dep_team = by_id[dep]["team"]
            if dep_team == t["team"]:
                continue
            on_critical_path = (
                is_critical[dep]
                and is_critical[tid]
                and earliest_finish[dep] == earliest_start[tid]
            )
            edges.append(
                {
                    "from": dep,
                    "from_team": dep_team,
                    "from_summary": by_id[dep]["summary"],
                    "to": tid,
                    "to_team": t["team"],
                    "to_summary": t["summary"],
                    "on_critical_path": on_critical_path,
                    "min_slack": min(slack[dep], slack[tid]),
                    "risk": t.get("risk") or by_id[dep].get("risk"),
                }
            )
    return edges


def write_schedule_json(sched: dict, outdir: Path) -> None:
    by_id = sched["by_id"]
    start_date = sched["start_date"]
    out = {"start_date": start_date.isoformat(), "tasks": []}
    for tid in sched["order"]:
        t = by_id[tid]
        out["tasks"].append(
            {
                "id": tid,
                "summary": t["summary"],
                "team": t["team"],
                "story_points": t["story_points"],
                "duration_days": sched["duration"][tid],
                "earliest_start": add_business_days(
                    start_date, sched["earliest_start"][tid]
                ).isoformat(),
                "earliest_finish": add_business_days(
                    start_date, sched["earliest_finish"][tid]
                ).isoformat(),
                "latest_start": add_business_days(
                    start_date, sched["latest_start"][tid]
                ).isoformat(),
                "latest_finish": add_business_days(
                    start_date, sched["latest_finish"][tid]
                ).isoformat(),
                "slack_days": sched["slack"][tid],
                "is_critical": sched["is_critical"][tid],
                "risk": t.get("risk"),
            }
        )
    (outdir / "schedule.json").write_text(json.dumps(out, indent=2) + "\n")


def write_gantt(sched: dict, data: dict, outdir: Path) -> None:
    by_id = sched["by_id"]
    start_date = sched["start_date"]

    by_team = defaultdict(list)
    for tid in sched["order"]:
        by_team[by_id[tid]["team"]].append(tid)

    lines = ["gantt", f'    title {data.get("project", "Untitled")} — Critical Path Schedule']
    lines.append("    dateFormat  YYYY-MM-DD")
    lines.append("    axisFormat  %m/%d")
    lines.append("    excludes    weekends")
    lines.append("")

    for team in sorted(by_team):
        lines.append(f"    section {team}")
        for tid in by_team[team]:
            label = by_id[tid]["summary"].replace(",", " -").replace(":", "-")
            task_start = add_business_days(start_date, sched["earliest_start"][tid])
            duration = sched["duration"][tid]
            status = "crit, " if sched["is_critical"][tid] else ""
            lines.append(
                f"    {label} :{status}{tid}, {task_start.isoformat()}, {duration}d"
            )
        lines.append("")

    (outdir / "gantt.mmd").write_text("\n".join(lines) + "\n")


def write_critical_path_md(sched: dict, data: dict, outdir: Path, threshold: int) -> None:
    by_id = sched["by_id"]
    start_date = sched["start_date"]
    project_duration = sched["project_duration"]
    finish_date = add_business_days(start_date, project_duration)
    chains = critical_path_chains(sched)
    edges = cross_team_edges(sched)
    on_path_count = sum(1 for e in edges if e["on_critical_path"])

    lines = [f'# Critical Path — {data.get("project", "Untitled")}', ""]
    lines.append(f"- Start date: **{start_date.isoformat()}** (rolled to nearest business day)")
    lines.append(f"- Finish date: **{finish_date.isoformat()}** ({project_duration} business days)")
    lines.append("")
    lines.append("## Velocity assumptions")
    lines.append("")
    lines.append("| Team | Points/day |")
    lines.append("|---|---|")
    for team, rate in sorted(sched["rates"].items()):
        lines.append(f"| {team} | {rate} |")
    lines.append("")
    lines.append(
        "These are assumptions, not measured facts — sanity-check them against real "
        "team velocity before treating the finish date above as a commitment."
    )
    lines.append("")

    lines.append("## Critical path")
    lines.append("")
    if not chains:
        lines.append("No tasks — nothing to schedule.")
    for i, chain in enumerate(chains, 1):
        prefix = f"Chain {i}: " if len(chains) > 1 else ""
        chain_str = " → ".join(
            f'{tid} ({by_id[tid]["summary"]}, {sched["duration"][tid]}d)' for tid in chain
        )
        lines.append(f"- {prefix}{chain_str}")
    lines.append("")

    near_critical = sorted(
        (
            tid
            for tid in by_id
            if 0 < sched["slack"][tid] <= threshold
        ),
        key=lambda tid: sched["slack"][tid],
    )
    lines.append(f"## Near-critical watch list (slack ≤ {threshold} business days)")
    lines.append("")
    if near_critical:
        lines.append("| Task | Summary | Slack (days) |")
        lines.append("|---|---|---|")
        for tid in near_critical:
            lines.append(f'| {tid} | {by_id[tid]["summary"]} | {sched["slack"][tid]} |')
    else:
        lines.append("None — every task is either critical or has comfortable slack.")
    lines.append("")

    lines.append("## Cross-team handoffs")
    lines.append("")
    lines.append(
        f"{len(edges)} cross-team dependency edges total, {on_path_count} of them "
        "directly on the critical path. See `risk_register.md` for the full list."
    )
    lines.append("")

    (outdir / "critical_path.md").write_text("\n".join(lines) + "\n")


def write_risk_register_md(sched: dict, data: dict, outdir: Path, threshold: int) -> None:
    edges = cross_team_edges(sched)
    edges.sort(key=lambda e: (not e["on_critical_path"], e["min_slack"]))

    lines = [f'# Dependency Risk Register — {data.get("project", "Untitled")}', ""]
    lines.append(
        "Every dependency edge that crosses a team boundary, ranked by schedule risk."
    )
    lines.append("")
    lines.append("| From (team) | To (team) | Status | Slack | Risk |")
    lines.append("|---|---|---|---|---|")
    for e in edges:
        if e["on_critical_path"]:
            status = "on critical path"
        elif e["min_slack"] <= threshold:
            status = "near-critical"
        else:
            status = "off path"
        lines.append(
            f'| {e["from"]} ({e["from_team"]}) → {e["to"]} ({e["to_team"]}) | '
            f'{e["from_summary"]} → {e["to_summary"]} | {status} | '
            f'{e["min_slack"]}d | {e["risk"] or "—"} |'
        )
    lines.append("")

    (outdir / "risk_register.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks_json", type=Path)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument(
        "--near-critical-threshold", type=int, default=DEFAULT_NEAR_CRITICAL_THRESHOLD
    )
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    try:
        data = load_and_validate(args.tasks_json)
        sched = compute_schedule(data)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    write_schedule_json(sched, args.outdir)
    write_gantt(sched, data, args.outdir)
    write_critical_path_md(sched, data, args.outdir, args.near_critical_threshold)
    write_risk_register_md(sched, data, args.outdir, args.near_critical_threshold)

    finish = add_business_days(sched["start_date"], sched["project_duration"])
    print(
        f"Scheduled {len(sched['by_id'])} tasks — finish {finish.isoformat()} "
        f"({sched['project_duration']} business days) — output in {args.outdir}"
    )


if __name__ == "__main__":
    main()
