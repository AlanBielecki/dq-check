"""Generate a small fake risk-control register with typical problems in it.

All data is made up. Run from the repo root:
    python examples/make_sample_data.py
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
n = 200

areas = ["Credit Risk", "Market Risk", "Operational Risk", "Liquidity Risk"]
statuses = ["Open", "In progress", "Closed"]

df = pd.DataFrame({
    "control_id": [f"CTRL-{i:04d}" for i in range(1, n + 1)],
    "risk_area": rng.choice(areas, n),
    "owner": rng.choice(["Anna K.", "Piotr W.", "Marta S.", "Tomasz L.", "Ewa N."], n),
    "status": rng.choice(statuses, n, p=[0.3, 0.3, 0.4]),
    "exposure_eur": rng.lognormal(mean=11, sigma=0.6, size=n).round(2),
    "score": rng.integers(1, 6, n),
    "opened": pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 400, n), unit="D"),
})
df["due"] = df["opened"] + pd.to_timedelta(rng.integers(14, 120, n), unit="D")

# --- the problems a real extract usually has ---
df.loc[[5, 40, 77], "risk_area"] = ["credit risk", "Credit  Risk ", "Crédit Risk"]
df.loc[[12, 13], "owner"] = None
df.loc[60, "status"] = "Done"
df.loc[[90, 150], "exposure_eur"] = [4_800_000, 6_250_000]
df.loc[33, "score"] = 9
df.loc[120, "due"] = df.loc[120, "opened"] - pd.Timedelta(days=10)
df.loc[180, "control_id"] = "CTRL-0011"
df = pd.concat([df, df.iloc[[25]]], ignore_index=True)

df.to_csv("examples/controls.csv", index=False)
print(f"saved examples/controls.csv ({len(df)} rows)")
