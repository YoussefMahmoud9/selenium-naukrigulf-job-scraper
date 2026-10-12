from __future__ import annotations

from dataclasses import dataclass


CSV_COLUMNS = [
    "job_title",
    "company_name",
    "job_location",
    "required_experience",
    "full_job_description",
]


@dataclass
class JobSummary:
    job_title: str
    company_name: str
    job_location: str
    required_experience: str
    detail_url: str
    source_page: int


@dataclass
class JobRecord:
    job_title: str
    company_name: str
    job_location: str
    required_experience: str
    full_job_description: str
    source_page: int
    detail_url: str
    error: str = ""

    def to_csv_row(self) -> dict[str, str]:
        return {
            "job_title": self.job_title,
            "company_name": self.company_name,
            "job_location": self.job_location,
            "required_experience": self.required_experience,
            "full_job_description": self.full_job_description,
        }

    @property
    def is_complete(self) -> bool:
        return all(self.to_csv_row().values())
