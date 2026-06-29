import subprocess
from sklearn.datasets import fetch_california_housing

from nexora import Nexora

data = fetch_california_housing(as_frame=True)
df = data.frame
df.to_csv("test_data.csv", index=False)

nx = Nexora("test_data.csv", target="MedHouseVal")
report = nx.quick()

assert report.best_model is not None,  "FAIL: best_model is None"
assert report.best_score > 0,          "FAIL: best_score <= 0"

report.save_code("model.py")
result = subprocess.run(["python", "model.py"], capture_output=True, text=True)
assert result.returncode == 0, f"FAIL: generated code crashed:\n{result.stderr}"

report.save("session.nx")
loaded = Nexora.load("session.nx")
assert loaded.best_model == report.best_model, "FAIL: session not restored"

report.decisions()
report.explain()

print("\n✓ All smoke tests passed")
