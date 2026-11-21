"""Individual data quality checks.

Every check takes a DataFrame (plus its own settings) and returns a list of
Issue objects. Checks never modify the data.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Issue:
    check: str
    column: str | None
    message: str
    rows: list[int] = field(default_factory=list)
    severity: str = "warning"  # "warning" or "error"


def missing_values(df: pd.DataFrame, max_share: float = 0.0, columns=None) -> list[Issue]:
    issues = []
    for col in columns or df.columns:
        mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        share = mask.mean()
        if share > max_share:
            issues.append(Issue(
                check="missing_values",
                column=col,
                message=f"{mask.sum()} missing ({share:.1%}, limit {max_share:.0%})",
                rows=df.index[mask].tolist(),
                severity="error" if share > 0.2 else "warning",
            ))
    return issues


def duplicate_rows(df: pd.DataFrame) -> list[Issue]:
    mask = df.duplicated(keep="first")
    if not mask.any():
        return []
    return [Issue(
        check="duplicate_rows",
        column=None,
        message=f"{mask.sum()} row(s) duplicated exactly",
        rows=df.index[mask].tolist(),
    )]


def duplicate_keys(df: pd.DataFrame, key: str | list[str]) -> list[Issue]:
    key = [key] if isinstance(key, str) else list(key)
    mask = df.duplicated(subset=key, keep=False)
    if not mask.any():
        return []
    return [Issue(
        check="duplicate_keys",
        column=", ".join(key),
        message=f"{df.loc[mask, key].drop_duplicates().shape[0]} key values used more than once",
        rows=df.index[mask].tolist(),
        severity="error",
    )]


def normalize_label(value) -> str:
    """Lowercase, drop accents and punctuation, collapse spaces.

    'Credit Risk - Retail', 'credit risk/retail ' and 'Crédit risk retail'
    all become 'credit risk retail'.
    """
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", " ", text.casefold())
    return re.sub(r"\s+", " ", text).strip()


def near_duplicate_labels(df: pd.DataFrame, column: str) -> list[Issue]:
    """Find values that are spelled differently but mean the same thing.

    This is the kind of problem that quietly creates two categories in a
    report where there should be one.
    """
    values = df[column].dropna().astype(str)
    groups = values.groupby(values.map(normalize_label)).unique()
    issues = []
    for norm, variants in groups.items():
        if len(variants) > 1:
            same = values[values.map(normalize_label) == norm]
            main = same.value_counts().idxmax()
            # flag only the rows that don't use the most common spelling
            rows = same.index[same != main].tolist()
            others = ", ".join(f"'{v}'" for v in sorted(variants) if v != main)
            issues.append(Issue(
                check="near_duplicate_labels",
                column=column,
                message=f"'{main}' is also written as {others}",
                rows=rows,
            ))
    return issues


def allowed_values(df: pd.DataFrame, column: str, allowed: list) -> list[Issue]:
    mask = df[column].notna() & ~df[column].isin(allowed)
    if not mask.any():
        return []
    bad = sorted(df.loc[mask, column].astype(str).unique())
    return [Issue(
        check="allowed_values",
        column=column,
        message=f"values outside the allowed list: {', '.join(bad)}",
        rows=df.index[mask].tolist(),
        severity="error",
    )]


def value_range(df: pd.DataFrame, column: str, min=None, max=None) -> list[Issue]:
    values = pd.to_numeric(df[column], errors="coerce")
    mask = pd.Series(False, index=df.index)
    if min is not None:
        mask |= values < min
    if max is not None:
        mask |= values > max
    if not mask.any():
        return []
    return [Issue(
        check="value_range",
        column=column,
        message=f"{mask.sum()} value(s) outside [{min}, {max}]",
        rows=df.index[mask].tolist(),
        severity="error",
    )]


def outliers_iqr(df: pd.DataFrame, column: str, k: float = 1.5) -> list[Issue]:
    """Flag values far outside the middle 50% of the data (Tukey's fences)."""
    values = pd.to_numeric(df[column], errors="coerce")
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0:
        return []
    low, high = q1 - k * iqr, q3 + k * iqr
    mask = (values < low) | (values > high)
    if not mask.any():
        return []
    return [Issue(
        check="outliers_iqr",
        column=column,
        message=f"{mask.sum()} value(s) outside [{low:,.2f}, {high:,.2f}]",
        rows=df.index[mask].tolist(),
    )]


def date_order(df: pd.DataFrame, start: str, end: str) -> list[Issue]:
    s = pd.to_datetime(df[start], errors="coerce")
    e = pd.to_datetime(df[end], errors="coerce")
    mask = s.notna() & e.notna() & (e < s)
    if not mask.any():
        return []
    return [Issue(
        check="date_order",
        column=f"{start} -> {end}",
        message=f"{mask.sum()} row(s) where {end} is before {start}",
        rows=df.index[mask].tolist(),
        severity="error",
    )]


CHECKS = {
    "missing_values": missing_values,
    "duplicate_rows": duplicate_rows,
    "duplicate_keys": duplicate_keys,
    "near_duplicate_labels": near_duplicate_labels,
    "allowed_values": allowed_values,
    "value_range": value_range,
    "outliers_iqr": outliers_iqr,
    "date_order": date_order,
}
