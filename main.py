from __future__ import annotations

import argparse

from naukrigulf_scraper.scraper import configure_logging, scrape_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Data Engineer jobs from Naukrigulf.")
    parser.add_argument("--pages", type=int, default=3, help="Number of search-result pages to scrape.")
    parser.add_argument("--output", default="data_engineer_jobs.csv", help="CSV output path.")
    parser.add_argument("--show-browser", action="store_true", help="Run Chrome visibly instead of headless.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between detail-page requests.")
    parser.add_argument("--sleep", type=float, default=5.0, help="Seconds to wait after every page navigation.")
    parser.add_argument("--profile-dir", help="Optional Chrome profile directory, useful for a fresh visible test.")
    args = parser.parse_args()

    configure_logging()
    result = scrape_jobs(
        max_pages=args.pages,
        output_path=args.output,
        headless=not args.show_browser,
        delay_seconds=args.delay,
        navigation_sleep_seconds=args.sleep,
        profile_dir=args.profile_dir,
    )

    print(f"Pages processed: {result.pages_processed}")
    print(f"Listings collected: {len(result.records)}")
    print(f"Incomplete records: {len(result.incomplete_records)}")
    if result.failure_reason:
        print(f"Scraping stopped because the page could not be loaded: {result.failure_reason}.")
    elif result.blocked:
        print("Scraping stopped because the website reported an access restriction.")


if __name__ == "__main__":
    main()
