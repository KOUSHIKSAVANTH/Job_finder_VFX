import re

from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup


class JobExtractor:

    def __init__(
        self,
        browser,
        log=print
    ):

        self.browser = browser
        self.log = log

    def extract(self, job):

        url = job["url"]
        snippet = str(
            job.get("snippet", "")
        )
        post_emails = list(set(
            re.findall(
                r"[A-Za-z0-9._%+-]+@"
                r"[A-Za-z0-9.-]+"
                r"\.[A-Za-z]{2,}",
                snippet
            )
        ))

        self.log(
            f"Inspecting: {url}"
        )

        try:
            page = self.browser.open(url)
            soup = BeautifulSoup(
                page.content(),
                "html.parser"
            )

            text = soup.get_text(
                " ",
                strip=True
            )

            emails = list(set(
                re.findall(
                    r"[A-Za-z0-9._%+-]+@"
                    r"[A-Za-z0-9.-]+"
                    r"\.[A-Za-z]{2,}",
                    " ".join([snippet, text])
                )
            ))

            application_links = []

            for link in soup.find_all(
                "a",
                href=True
            ):
                application_url = urljoin(
                    url,
                    link["href"]
                )

                if urlsplit(application_url).scheme not in [
                    "http",
                    "https"
                ]:
                    continue

                label = link.get_text(
                    " ",
                    strip=True
                ).lower()

                score = 0

                if "apply" in label:
                    score += 4
                if "application" in label:
                    score += 3
                if "career" in label:
                    score += 2
                if "job" in label:
                    score += 1

                if score:
                    application_links.append(
                        (score, application_url)
                    )

            application_links = [
                application_url
                for _, application_url in sorted(
                    set(application_links),
                    key=lambda item: item[0],
                    reverse=True
                )
            ]

            return {
                "page_url": page.url,
                "emails": emails,
                "post_emails": post_emails,
                "application_links": application_links
            }

        except Exception as error:
            self.log(
                f"Extraction error: {error}"
            )

            return {
                "page_url": url,
                "emails": [],
                "post_emails": post_emails,
                "application_links": []
            }