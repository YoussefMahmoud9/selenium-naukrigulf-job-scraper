from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import CSV_COLUMNS, JobRecord


def export_jobs_csv(records: list[JobRecord], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [record.to_csv_row() for record in records]
    jobs = pd.DataFrame(rows, columns=CSV_COLUMNS)
    jobs.to_csv(path, index=False, encoding="utf-8")
