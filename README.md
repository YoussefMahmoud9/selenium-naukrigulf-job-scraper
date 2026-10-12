# Naukrigulf Data Engineer Job Scraper

Selenium scraper for the DEPI Python Advanced assignment. It searches Naukrigulf for Data Engineer jobs, processes the first three result pages, opens each detail page, and exports:

- `job_title`
- `company_name`
- `job_location`
- `required_experience`
- `full_job_description`

## Setup

```powershell
cd E:\Depi\Techincal\DEPI-Projects\selenium-naukrigulf-job-scraper
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Chrome or another Selenium-supported browser must be installed. Selenium Manager is used to obtain a compatible driver if needed.

## Run

```powershell
$env:PYTHONPATH = "src"
python main.py --pages 3 --output data_engineer_jobs.csv --sleep 5
```

Use `--show-browser` to run with a visible browser. If Naukrigulf shows CAPTCHA, access-denied, or similar anti-bot protection, stop and do not bypass it.

The scraper waits 5 seconds after each navigation by default. Change this with `--sleep`; use `--profile-dir` when you want to provide a fresh Chrome profile for a visible test.

The scraper distinguishes access restrictions from browser/network load failures. A Chromium error page such as `ERR_HTTP2_PROTOCOL_ERROR` is reported as a page-load failure and produces no fabricated records.

## Verified Local Result

The completed visible-Chrome run processed search-result pages 1, 2, and 3 and exported 90 genuine job records with 90 non-empty full descriptions. The generated `data_engineer_jobs.csv` is intentionally excluded from the public repository because it contains scraped third-party content. Re-run the scraper locally to regenerate it; current listings and descriptions may change.

The scraper does not bypass CAPTCHA, access controls, or anti-bot protections. It logs incomplete records when a source field is missing and continues with other listings.

## Tests

```powershell
python -m pytest
```

Tests use local HTML snippets and do not access the live website.
