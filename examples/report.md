# Data quality report: controls.csv

201 rows, 8 columns. 4 errors, 4 warnings, 15 rows flagged.

| Severity | Check | Column | Details | Rows |
|---|---|---|---|---|
| error | allowed_values | status | values outside the allowed list: Done | 60 |
| error | date_order | opened -> due | 1 row(s) where due is before opened | 120 |
| error | duplicate_keys | control_id | 2 key values used more than once | 10, 25, 180, 200 |
| error | value_range | score | 1 value(s) outside [1, 5] | 33 |
| warning | duplicate_rows | - | 1 row(s) duplicated exactly | 200 |
| warning | missing_values | owner | 2 missing (1.0%, limit 0%) | 12, 13 |
| warning | near_duplicate_labels | risk_area | 'Credit Risk' is also written as 'Credit  Risk ', 'Crédit Risk', 'credit risk' | 5, 40, 77 |
| warning | outliers_iqr | exposure_eur | 3 value(s) outside [-88,718.45, 199,399.24] | 23, 90, 150 |
