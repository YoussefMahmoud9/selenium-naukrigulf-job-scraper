from __future__ import annotations

from naukrigulf_scraper.parser import detect_blocked_page, detect_page_issue, parse_job_description, parse_search_results


SEARCH_HTML = """
<html><body>
  <div class="job">
    <a href="/data-engineer-jobs-in-dubai-uae-in-dicetek-llc-5-to-8-years-m-cd-41691-jid-290926000088">Data Engineer</a>
    <a href="/dicetek-jobs">Dicetek LLC</a>
    <ul><li>5 - 8 Years</li><li>Dubai - United Arab Emirates (UAE)</li></ul>
    <p>Develop ETL pipelines.</p>
  </div>
</body></html>
"""


DETAIL_HTML = """
<html><body>
<h1>Data Engineer</h1>
<div>Experience</div><div>5 - 8 Years</div>
<h2>Job Description</h2>
<h3>Roles & Responsibilities</h3>
<ul><li>Build scalable ETL pipelines.</li><li>Implement data quality checks.</li></ul>
<h2>Skills</h2>
<p>Python</p>
</body></html>
"""


def test_parse_search_results_extracts_required_summary_fields():
    records = parse_search_results(SEARCH_HTML, page_number=1)

    assert len(records) == 1
    assert records[0].job_title == "Data Engineer"
    assert records[0].company_name == "Dicetek LLC"
    assert records[0].required_experience == "5 - 8 Years"
    assert records[0].job_location == "Dubai - United Arab Emirates (UAE)"
    assert records[0].detail_url.startswith("https://www.naukrigulf.com/")


def test_parse_search_results_handles_missing_fields():
    html = '<a href="/unknown-jid-123">Untitled Data Job</a>'

    records = parse_search_results(html, page_number=2)

    assert len(records) == 1
    assert records[0].job_title == "Untitled Data Job"
    assert records[0].company_name == ""
    assert records[0].required_experience == ""
    assert records[0].job_location == ""


def test_parse_job_description_stops_before_skills():
    description = parse_job_description(DETAIL_HTML)

    assert "Build scalable ETL pipelines." in description
    assert "Implement data quality checks." in description
    assert "Python" not in description


def test_detect_blocked_page_detects_chrome_network_error_document():
    html = '<div class="error-code">ERR_CONNECTION_CLOSED</div>'

    assert detect_blocked_page(html)
    assert detect_page_issue(html) == "browser network error ERR_CONNECTION_CLOSED"
