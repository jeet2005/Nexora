"""Session serialization for Nexora reports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import joblib

if TYPE_CHECKING:
    from nexora.report import NexoraReport


def save_report(report: "NexoraReport", path: str | Path) -> Path:
    """Persist a report to a `.nx` session file.

    Args:
        report: Trained report to persist.
        path: Destination file path.

    Returns:
        Resolved path written to disk.

    Example:
        `save_report(report, "session.nx")`
    """

    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(report, output)
    return output


def load_report(path: str | Path) -> "NexoraReport":
    """Load a `.nx` session file as a ready NexoraReport.

    Args:
        path: Session file created by `report.save(...)`.

    Returns:
        Loaded NexoraReport.

    Example:
        `report = load_report("session.nx")`
    """

    session = Path(path).expanduser().resolve()
    if not session.exists():
        raise FileNotFoundError(f"Nexora session does not exist: {session}")
    report = joblib.load(session)
    from nexora.report import NexoraReport

    if not isinstance(report, NexoraReport):
        raise TypeError(f"File is not a NexoraReport session: {session}")
    return report
