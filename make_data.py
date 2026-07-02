import numpy as np
import pandas as pd

# Generate a synthetic dataset for testing
np.random.seed(42)
n_samples = 100

data = {
    "price": np.random.uniform(10, 100, n_samples),
    "category": np.random.choice(["A", "B", "C"], n_samples),
    "is_active": np.random.choice([True, False], n_samples),
    "target": np.random.uniform(0, 1, n_samples),
}

df = pd.DataFrame(data)
df.to_csv("test_data.csv", index=False)
print("Created test_data.csv")
