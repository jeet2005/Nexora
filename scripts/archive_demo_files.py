"""Safe cleanup script: moves notebooks and demo artifacts to examples/archive/ with timestamp."""

import shutil
from datetime import datetime
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    examples = root / "examples"
    archive = examples / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    targets = [p for p in examples.glob("*.ipynb")] + list(
        (examples / "codegen_demo").glob("**/*")
    )
    moved = 0
    for t in targets:
        if t.is_file():
            dest = archive / f"{ts}_{t.name}"
            shutil.move(str(t), str(dest))
            moved += 1
    print(f"Archived {moved} files to {archive}")


if __name__ == "__main__":
    main()
