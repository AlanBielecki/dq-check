from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .checks import CHECKS, Issue


def load_rules(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        rules = json.load(f)
    for rule in rules:
        if rule.get("check") not in CHECKS:
            raise ValueError(f"unknown check: {rule.get('check')!r}")
    return rules


def run(df: pd.DataFrame, rules: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    for rule in rules:
        params = {k: v for k, v in rule.items() if k != "check"}
        issues.extend(CHECKS[rule["check"]](df, **params))
    return issues


def to_markdown(issues: list[Issue], df: pd.DataFrame, source: str = "") -> str:
    errors = sum(i.severity == "error" for i in issues)
    warnings = len(issues) - errors
    flagged = len({r for i in issues for r in i.rows})

    lines = [f"# Data quality report{f': {source}' if source else ''}", ""]
    lines.append(f"{len(df)} rows, {len(df.columns)} columns. "
                 f"{errors} errors, {warnings} warnings, {flagged} rows flagged.")
    lines.append("")
    if not issues:
        lines.append("No issues found.")
        return "\n".join(lines) + "\n"

    lines += ["| Severity | Check | Column | Details | Rows |",
              "|---|---|---|---|---|"]
    order = {"error": 0, "warning": 1}
    for i in sorted(issues, key=lambda x: (order[x.severity], x.check)):
        rows = ", ".join(map(str, i.rows[:8])) + (" ..." if len(i.rows) > 8 else "")
        lines.append(f"| {i.severity} | {i.check} | {i.column or '-'} | {i.message} | {rows} |")
    return "\n".join(lines) + "\n"
