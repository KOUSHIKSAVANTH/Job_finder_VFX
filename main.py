import json
import os

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from database import Database

from discovery.search import JobSearch
from discovery.extractor import JobExtractor

from application.browser import Browser
from application.router import (
    ApplicationRouter
)

from report import get_applied_urls, write_report


def log(message):

    print(
        f"[AUTOPILOT] {message}"
    )


def load_config():

    with open(
        "config.json",
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def main():

    # Load .env from the same folder as main.py
    env_path = Path(__file__).resolve().parent / ".env"

    env_loaded = load_dotenv(
        dotenv_path=env_path
    )

    print(
        "ENV FILE:",
        env_path
    )

    print(
        "ENV FILE EXISTS:",
        env_path.exists()
    )

    print(
        "ENV LOADED:",
        env_loaded
    )

    print(
        "TAVILY VARIABLE EXISTS:",
        "TAVILY_API_KEY" in os.environ
    )

    print(
        "TAVILY KEY FOUND:",
        bool(
            os.getenv(
                "TAVILY_API_KEY"
            )
        )
    )

    config = load_config()

    profile = config["profile"]

    preferences = (
        config["job_preferences"]
    )

    print(
        "AUTO SUBMIT:",
        preferences.get(
            "auto_submit",
            False
        )
    )

    print(
        "RETRY MANUAL:",
        preferences.get(
            "retry_manual",
            False
        )
    )

    database = Database()

    browser = Browser()

    try:

        log(
            "Starting Job Finder Autopilot..."
        )

        search = JobSearch(
            preferences,
            log
        )

        jobs = search.discover()

        log(
            f"Discovered {len(jobs)} jobs."
        )

        extractor = JobExtractor(
            browser,
            log
        )

        router = ApplicationRouter(
            browser,
            profile,
            log,
            auto_submit=preferences.get(
                "auto_submit",
                False
            )
        )

        skipped_count = 0
        result_counts = {}
        report_rows = []
        run_time = datetime.now().isoformat(
            timespec="seconds"
        )
        retry_manual = preferences.get(
            "retry_manual",
            False
        )
        applied_urls = get_applied_urls(Path(__file__).resolve().parent)

        for number, job in enumerate(
            jobs,
            start=1
        ):

            url = job["url"]

            if url in applied_urls:
                skipped_count += 1
                log(
                    f"Skipping marked applied in Excel: {url}"
                )
                report_rows.append({
                    "run_time": run_time,
                    "change": "Filtered by Excel",
                    "status": "Applied (manual)",
                    "title": job.get("title", ""),
                    "role": job.get("role", ""),
                    "url": url,
                    "source": job.get("source", ""),
                    "details": "Skipped because the Excel 'Applied?' column says Applied.",
                    "applied_status": "Applied"
                })
                continue

            title = job.get(
                "title",
                ""
            )

            previous_status = database.get_status(
                url
            )

            terminal_statuses = [
                "Applied",
                "Sent"
            ]

            if not retry_manual:
                terminal_statuses.append(
                    "Manual Required"
                )

            if previous_status in terminal_statuses:

                skipped_count += 1

                log(
                    f"Skipping {previous_status.lower()}: "
                    f"{url}"
                )

                report_rows.append({
                    "run_time": run_time,
                    "change": "Already recorded",
                    "status": previous_status,
                    "title": title,
                    "role": job.get("role", ""),
                    "url": url,
                    "source": job.get("source", ""),
                    "details": "Skipped by database history."
                })

                continue

            if previous_status == "Manual Required":
                log(
                    f"Retrying manual record: {url}"
                )

            log(
                f"\n[{number}/{len(jobs)}]"
            )

            log(
                f"Job: {title}"
            )

            log(
                f"URL: {url}"
            )

            database.add(

                url=url,

                title=title,

                source=job.get(
                    "source",
                    "Search"
                ),

                status="Processing"
            )

            try:

                extracted = extractor.extract(
                    job
                )

                status, details = router.apply(

                    url=url,

                    application_links=extracted[
                        "application_links"
                    ],

                    company="Unknown Company",

                    role=title,

                    emails=extracted["emails"],

                    post_emails=extracted[
                        "post_emails"
                    ],

                    linkedin_post=job.get(
                        "is_linkedin_post",
                        False
                    )
                )

                database.update_status(

                    url,

                    status,

                    details
                )

                result_counts[status] = (
                    result_counts.get(status, 0) + 1
                )

                log(
                    f"RESULT: {status}"
                )

                log(
                    details
                )

                report_rows.append({
                    "run_time": run_time,
                    "change": (
                        "Updated" if previous_status
                        else "New opportunity"
                    ),
                    "status": status,
                    "title": title,
                    "role": job.get("role", ""),
                    "url": url,
                    "source": job.get("source", ""),
                    "emails": "; ".join(
                        extracted["emails"]
                    ),
                    "application_links": "; ".join(
                        extracted["application_links"]
                    ),
                    "details": details
                })

            except Exception as error:

                database.update_status(

                    url,

                    "Failed",

                    str(error)
                )

                log(
                    f"FAILED: {error}"
                )

                report_rows.append({
                    "run_time": run_time,
                    "change": (
                        "Updated" if previous_status
                        else "New opportunity"
                    ),
                    "status": "Failed",
                    "title": title,
                    "role": job.get("role", ""),
                    "url": url,
                    "source": job.get("source", ""),
                    "details": str(error)
                })

        current_report, history_report = write_report(
            report_rows
        )

        log(
            f"Excel report: {current_report}"
        )

        log(
            f"Report history: {history_report}"
        )

        log(
            "\nRun summary: "
            f"{skipped_count} already processed, "
            + ", ".join(
                f"{status}={count}"
                for status, count in result_counts.items()
            )
        )

        log(
            "Autopilot run completed."
        )

    finally:

        browser.close()

        database.close()


if __name__ == "__main__":

    main()