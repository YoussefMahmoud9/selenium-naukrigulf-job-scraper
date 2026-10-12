from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .exporter import export_jobs_csv
from .models import JobRecord, JobSummary
from .parser import build_search_url, detect_page_issue, parse_job_description, parse_search_results


LOGGER = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    records: list[JobRecord]
    pages_processed: list[int]
    blocked: bool = False
    failure_reason: str = ""

    @property
    def incomplete_records(self) -> list[JobRecord]:
        return [record for record in self.records if not record.is_complete or record.error]


def configure_logging(log_path: str | Path = "logs/scraper.log") -> None:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )


def create_driver(headless: bool = True, profile_dir: str | Path | None = None) -> WebDriver:
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if headless:
        options.add_argument("--headless=new")
    if profile_dir:
        options.add_argument(f"--user-data-dir={Path(profile_dir).resolve()}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def wait_for_results_page(driver: WebDriver, timeout: int = 20) -> None:
    WebDriverWait(driver, timeout).until(lambda d: "Data Engineer" in d.page_source)
    WebDriverWait(driver, timeout).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="-jid-"]')) > 0)


def wait_for_detail_page(driver: WebDriver, timeout: int = 20) -> None:
    WebDriverWait(driver, timeout).until(lambda d: "Job Description" in d.page_source or detect_page_issue(d.page_source))


def scrape_jobs(
    max_pages: int = 3,
    output_path: str | Path = "data_engineer_jobs.csv",
    headless: bool = True,
    delay_seconds: float = 1.0,
    navigation_sleep_seconds: float = 5.0,
    profile_dir: str | Path | None = None,
) -> ScrapeResult:
    driver = create_driver(headless=headless, profile_dir=profile_dir)
    records: list[JobRecord] = []
    pages_processed: list[int] = []
    seen_detail_urls: set[str] = set()

    try:
        for page_number in range(1, max_pages + 1):
            url = build_search_url(page_number)
            LOGGER.info("Loading search page %s: %s", page_number, url)
            driver.get(url)
            time.sleep(navigation_sleep_seconds)
            try:
                wait_for_results_page(driver)
            except TimeoutException:
                issue = detect_page_issue(driver.page_source)
                if issue:
                    LOGGER.error("Could not load search page %s: %s. Stopping.", page_number, issue)
                    return ScrapeResult(records=records, pages_processed=pages_processed, failure_reason=issue)
                LOGGER.exception("Timed out waiting for search results on page %s", page_number)
                continue

            issue = detect_page_issue(driver.page_source)
            if issue:
                LOGGER.error("Could not load search page %s: %s. Stopping.", page_number, issue)
                return ScrapeResult(records=records, pages_processed=pages_processed, failure_reason=issue)

            summaries = parse_search_results(driver.page_source, page_number)
            LOGGER.info("Found %s job summaries on page %s", len(summaries), page_number)
            pages_processed.append(page_number)

            for summary in summaries:
                if summary.detail_url in seen_detail_urls:
                    LOGGER.info("Skipping duplicate listing URL: %s", summary.detail_url)
                    continue
                seen_detail_urls.add(summary.detail_url)
                records.append(_scrape_detail(driver, summary, navigation_sleep_seconds))
                time.sleep(delay_seconds)

        export_jobs_csv(records, output_path)
        return ScrapeResult(records=records, pages_processed=pages_processed)
    finally:
        driver.quit()


def _scrape_detail(driver: WebDriver, summary: JobSummary, navigation_sleep_seconds: float) -> JobRecord:
    try:
        LOGGER.info("Loading detail page: %s", summary.detail_url)
        driver.get(summary.detail_url)
        time.sleep(navigation_sleep_seconds)
        wait_for_detail_page(driver)
        issue = detect_page_issue(driver.page_source)
        if issue:
            raise RuntimeError(issue)
        description = parse_job_description(driver.page_source)
        error = "" if description else "full job description not found"
    except (TimeoutException, WebDriverException, RuntimeError) as exc:
        LOGGER.exception("Could not scrape detail page for %s", summary.detail_url)
        description = ""
        error = str(exc)

    record = JobRecord(
        job_title=summary.job_title,
        company_name=summary.company_name,
        job_location=summary.job_location,
        required_experience=summary.required_experience,
        full_job_description=description,
        source_page=summary.source_page,
        detail_url=summary.detail_url,
        error=error,
    )
    if not record.is_complete:
        LOGGER.warning("Incomplete record from %s: %s", summary.detail_url, record)
    return record
