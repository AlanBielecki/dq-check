# dq-check

Small Python tool for checking the quality of tabular data before it goes into a report, a dashboard or a model.

I built it because the same problems keep showing up in data extracts I work with: one category written three different ways, IDs that are not unique, an end date before the start date, a status value nobody agreed on. Each one is easy to spot by hand in ten rows and easy to miss in ten thousand. Here the checks live in a JSON file, so the same rules can run on every new extract.

## Checks

| Check | What it finds |
|---|---|
| `missing_values` | empty or blank cells, with an optional allowed share |
| `duplicate_rows` | rows that are exact copies |
| `duplicate_keys` | IDs that should be unique but are not |
| `near_duplicate_labels` | the same value spelled differently (`Credit Risk`, `credit risk`, `Crédit  Risk `) |
| `allowed_values` | values outside an agreed list |
| `value_range` | numbers below a minimum or above a maximum |
| `outliers_iqr` | values far outside the typical range (Tukey's fences, `k` adjustable) |
| `date_order` | rows where one date is before the date it should follow |

`near_duplicate_labels` is the one I find most useful in practice. It lowercases, removes accents and punctuation, collapses spaces and then groups the values. Only the rows that don't use the most common spelling are flagged.

## Usage

```bash
pip install -e .
python examples/make_sample_data.py      # creates examples/controls.csv (fake data)
python -m dqcheck examples/controls.csv --rules examples/rules.json --out examples/report.md
```

Rules file:

```json
[
  {"check": "duplicate_keys", "key": "control_id"},
  {"check": "near_duplicate_labels", "column": "risk_area"},
  {"check": "allowed_values", "column": "status", "allowed": ["Open", "In progress", "Closed"]},
  {"check": "outliers_iqr", "column": "exposure_eur", "k": 3}
]
```

The command exits with code 1 when any check returns an error, so it can stop a pipeline before bad data moves on.

It can also be used from Python:

```python
import pandas as pd
from dqcheck import run, to_markdown, load_rules

df = pd.read_csv("examples/controls.csv")
issues = run(df, load_rules("examples/rules.json"))
print(to_markdown(issues, df))
```

## Example output

Result for the sample data (a made-up register of risk controls with a few problems added on purpose), see [examples/report.md](examples/report.md):

| Severity | Check | Column | Details | Rows |
|---|---|---|---|---|
| error | allowed_values | status | values outside the allowed list: Done | 60 |
| error | date_order | opened -> due | 1 row(s) where due is before opened | 120 |
| error | duplicate_keys | control_id | 2 key values used more than once | 10, 25, 180, 200 |
| error | value_range | score | 1 value(s) outside [1, 5] | 33 |
| warning | near_duplicate_labels | risk_area | 'Credit Risk' is also written as 'Credit  Risk ', 'Crédit Risk', 'credit risk' | 5, 40, 77 |
| warning | outliers_iqr | exposure_eur | 3 value(s) outside [-88,718.45, 199,399.24] | 23, 90, 150 |

## Tests

```bash
pip install pytest
pytest
```

## Ideas for later

- HTML report with the flagged rows shown
- fuzzy matching (edit distance) for typos that normalization doesn't catch
- reading rules from a SharePoint list, so business users can maintain them
