import json

from dotenv import load_dotenv

from database import Database

from discovery.search import JobSearch
from discovery.extractor import JobExtractor

from application.browser import Browser
from application.router import (
    ApplicationRouter
)


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

    load_dotenv()

    config = load_config()

    profile = config["profile"]

    preferences = (
        config["job_preferences"]
    )

    database = Database()

    browser = Browser()

    try:

        log("Starting Job Finder Autopilot...")

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
            log
        )

        for number, job in enumerate(
            jobs,
            start=1
        ):

            url = job["url"]

            title = job.get(
                "title",
                ""
            )

            if database.exists(url):

                log(
                    f"Skipping duplicate: {url}"
                )

                continue

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

                    company="Unknown Company",

                    role=title,

                    emails=extracted["emails"]
                )

                database.update_status(

                    url,

                    status,

                    details
                )

                log(
                    f"RESULT: {status}"
                )

                log(
                    details
                )

            except Exception as error:

                database.update_status(

                    url,

                    "Failed",

                    str(error)
                )

                log(
                    f"FAILED: {error}"
                )

        log(
            "\nAutopilot run completed."
        )

    finally:

        browser.close()

        database.close()


if __name__ == "__main__":

    main()