from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import JobSummary


BASE_URL = "https://www.naukrigulf.com"
YEARS_PATTERN = re.compile(r"\b\d+\s*-\s*\d+\s*Years\b|\b\d+\+?\s*Years\b", re.IGNORECASE)
CHROME_ERROR_PATTERN = re.compile(r"ERR_[A-Z0-9_]+")
NOISE_LINES = {
    "easy apply",
    "multiple vacancies",
    "employer active",
    "send me jobs like this",
    "login/register",
}


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _line_texts(element) -> list[str]:
    text = element.get_text("\n", strip=True)
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def _looks_like_company(text: str) -> bool:
    lowered = text.lower()
    if not text or YEARS_PATTERN.search(text):
        return False
    if any(token in lowered for token in ["united arab emirates", "saudi arabia", "qatar", "egypt", "lebanon", "morocco", "oman"]):
        return False
    if lowered in NOISE_LINES:
        return False
    return True


def build_search_url(page_number: int) -> str:
    if page_number <= 1:
        return f"{BASE_URL}/data-engineer-jobs"
    return f"{BASE_URL}/data-engineer-jobs-{page_number}"


def detect_blocked_page(html: str) -> bool:
    return detect_page_issue(html) is not None


def detect_page_issue(html: str) -> str | None:
    """Return a precise access/load issue when the page is not usable."""
    error_code = CHROME_ERROR_PATTERN.search(html)
    if error_code:
        return f"browser network error {error_code.group(0)}"

    lowered = html.lower()
    restriction_markers = {
        "captcha": "CAPTCHA or bot challenge",
        "access denied": "access denied",
        "unusual traffic": "unusual traffic restriction",
        "temporarily blocked": "temporary access restriction",
    }
    for marker, description in restriction_markers.items():
        if marker in lowered:
            return description
    return None


def parse_search_results(html: str, page_number: int, base_url: str = BASE_URL) -> list[JobSummary]:
    soup = BeautifulSoup(html, "lxml")
    summaries: list[JobSummary] = []
    seen_urls: set[str] = set()

    for link in soup.select('a[href*="-jid-"]'):
        href = link.get("href")
        title = clean_text(link.get_text(" ", strip=True))
        if not href or not title:
            continue

        detail_url = urljoin(base_url, href)
        if detail_url in seen_urls:
            continue
        seen_urls.add(detail_url)

        container = _nearest_job_container(link)
        lines = _line_texts(container)
        company = _company_after_title(lines, title)
        experience = _first_match(lines, YEARS_PATTERN)
        location = _location_after_experience(lines, experience)

        summaries.append(
            JobSummary(
                job_title=title,
                company_name=company,
                job_location=location,
                required_experience=experience,
                detail_url=detail_url,
                source_page=page_number,
            )
        )

    return summaries


def _nearest_job_container(link):
    for parent in link.parents:
        links = parent.select('a[href*="-jid-"]')
        text = parent.get_text(" ", strip=True)
        if len(links) == 1 and YEARS_PATTERN.search(text):
            return parent
    return link.parent or link


def _company_after_title(lines: list[str], title: str) -> str:
    for index, line in enumerate(lines):
        if line == title:
            for candidate in lines[index + 1 : index + 4]:
                if _looks_like_company(candidate):
                    return candidate
    for line in lines[:4]:
        if line != title and _looks_like_company(line):
            return line
    return ""


def _first_match(lines: list[str], pattern: re.Pattern[str]) -> str:
    for line in lines:
        match = pattern.search(line)
        if match:
            return clean_text(match.group(0))
    return ""


def _location_after_experience(lines: list[str], experience: str) -> str:
    if experience and experience in lines:
        index = lines.index(experience)
        if index + 1 < len(lines):
            return lines[index + 1]
    for line in lines:
        lowered = line.lower()
        if any(token in lowered for token in ["united arab emirates", "saudi arabia", "qatar", "egypt", "lebanon", "morocco", "oman", "india"]):
            return line
    return ""


def parse_job_description(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    lines = _line_texts(soup)
    start = _find_line_index(lines, "Job Description")
    if start is None:
        return ""

    stop_labels = {
        "skills",
        "employment type",
        "company industry",
        "department / functional area",
        "keywords",
    }
    description_lines: list[str] = []
    for line in lines[start + 1 :]:
        if line.strip().lower() in stop_labels:
            break
        if line.lower() in NOISE_LINES:
            continue
        description_lines.append(line)
    return clean_text(" ".join(description_lines))


def _find_line_index(lines: list[str], label: str) -> int | None:
    lowered = label.lower()
    for index, line in enumerate(lines):
        if line.lower() == lowered:
            return index
    return None
