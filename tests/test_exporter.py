from __future__ import annotations

import csv

from naukrigulf_scraper.exporter import export_jobs_csv
from naukrigulf_scraper.models import CSV_COLUMNS, JobRecord


def test_export_jobs_csv_writes_utf8_columns_and_rows(tmp_path):
    output = tmp_path / "jobs.csv"
    records = [
        JobRecord(
            job_title="Data Engineer",
            company_name="شركة Test",
            job_location="Dubai - United Arab Emirates (UAE)",
            required_experience="5 - 8 Years",
            full_job_description="Build ETL pipelines.",
            source_page=1,
            detail_url="https://example.com/job",
        )
    ]

    export_jobs_csv(records, output)

    with output.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)

    assert reader.fieldnames == CSV_COLUMNS
    assert rows[0]["company_name"] == "شركة Test"
    assert rows[0]["full_job_description"] == "Build ETL pipelines."
