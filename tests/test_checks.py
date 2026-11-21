import pandas as pd
import pytest

from dqcheck import checks, run
from dqcheck.runner import load_rules


@pytest.fixture
def df():
    return pd.DataFrame({
        "id": [1, 2, 3, 3, 5],
        "area": ["Credit Risk", "credit risk", "Market Risk", "Crédit-Risk", None],
        "status": ["Open", "Closed", "Done", "Open", "Open"],
        "amount": [100, 110, 95, 105, 10_000],
        "start": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01", "2025-05-01"],
        "end": ["2025-01-10", "2025-01-15", "2025-03-05", "2025-04-02", "2025-05-03"],
    })


def test_normalize_label():
    assert checks.normalize_label("  Crédit  Risk - Retail ") == "credit risk retail"
    assert checks.normalize_label(None) == ""


def test_missing_values(df):
    [issue] = checks.missing_values(df, columns=["area"])
    assert issue.rows == [4]


def test_duplicate_keys(df):
    [issue] = checks.duplicate_keys(df, "id")
    assert issue.rows == [2, 3]


def test_no_duplicate_rows(df):
    assert checks.duplicate_rows(df) == []


def test_near_duplicate_labels(df):
    [issue] = checks.near_duplicate_labels(df, "area")
    assert sorted(issue.rows) == [1, 3]


def test_allowed_values(df):
    [issue] = checks.allowed_values(df, "status", ["Open", "Closed"])
    assert issue.rows == [2]


def test_outliers(df):
    [issue] = checks.outliers_iqr(df, "amount")
    assert issue.rows == [4]


def test_date_order(df):
    [issue] = checks.date_order(df, "start", "end")
    assert issue.rows == [1]


def test_example_rules_load():
    rules = load_rules("examples/rules.json")
    assert {r["check"] for r in rules} <= set(checks.CHECKS)


def test_unknown_check(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text('[{"check": "nope"}]')
    with pytest.raises(ValueError):
        load_rules(path)


def test_run_collects_everything(df):
    rules = [{"check": "duplicate_keys", "key": "id"},
             {"check": "value_range", "column": "amount", "max": 1000}]
    assert [i.check for i in run(df, rules)] == ["duplicate_keys", "value_range"]
