import argparse
import sys
from pathlib import Path

import pandas as pd

from .runner import load_rules, run, to_markdown


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="dqcheck", description="Run data quality checks on a CSV file.")
    p.add_argument("csv", help="input CSV file")
    p.add_argument("--rules", required=True, help="JSON file with the list of checks")
    p.add_argument("--out", help="write the report to this file instead of stdout")
    p.add_argument("--sep", default=",", help="CSV separator (default: ,)")
    args = p.parse_args(argv)

    df = pd.read_csv(args.csv, sep=args.sep)
    issues = run(df, load_rules(args.rules))
    report = to_markdown(issues, df, source=Path(args.csv).name)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"Report saved to {args.out}")
    else:
        print(report)

    # non-zero exit code if there are errors, so it can be used in a pipeline
    return 1 if any(i.severity == "error" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
