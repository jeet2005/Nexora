from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def regression_csv(tmp_path):
    rng = np.random.default_rng(42)
    rows = 80
    age = rng.integers(22, 68, size=rows)
    income = rng.normal(72_000, 12_000, size=rows).round(2)
    region = rng.choice(["north", "south", "east"], size=rows)
    region_bonus = pd.Series(region).map({"north": 8.0, "south": -3.0, "east": 2.0}).to_numpy()
    revenue = (age * 2.4 + income * 0.012 + region_bonus + rng.normal(0, 3, rows)).round(2)
    df = pd.DataFrame(
        {
            "customer_id": [f"C{i:03d}" for i in range(rows)],
            "age": age,
            "income": income,
            "region": region,
            "signup_date": pd.date_range("2025-01-01", periods=rows).astype(str),
            "constant_flag": "keep",
            "revenue": revenue,
        }
    )
    path = tmp_path / "sales.csv"
    df.to_csv(path, index=False)
    return path, df


@pytest.fixture()
def classification_csv(tmp_path):
    rng = np.random.default_rng(7)
    rows = 72
    tenure = rng.integers(1, 48, size=rows)
    monthly_spend = rng.normal(95, 25, size=rows).round(2)
    plan = rng.choice(["basic", "pro", "enterprise"], size=rows)
    churn = np.where((tenure < 12) & (plan == "basic"), "yes", "no")
    df = pd.DataFrame(
        {
            "account_id": [f"A{i:03d}" for i in range(rows)],
            "tenure": tenure,
            "monthly_spend": monthly_spend,
            "plan": plan,
            "churn": churn,
        }
    )
    path = tmp_path / "churn.csv"
    df.to_csv(path, index=False)
    return path, df
