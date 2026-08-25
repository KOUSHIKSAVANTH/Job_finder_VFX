import re

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

        self.log(
            f"Inspecting: {url}"
        )

        try:

            page = self.browser.open(url)

            html = page.content()

            soup = BeautifulSoup(
                html,
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
                    text
                )
            ))

            application_links = []

            for link in soup.find_all(
                "a",
                href=True
            ):

                href = link["href"]

                label = link.get_text(
                    " ",
                    strip=True
                ).lower()

                if any(word in label for word in [
                    "apply",
                    "application",
                    "careers",
                    "job"
                ]):

                    application_links.append(
                        href
                    )

            return {

                "page_url": url,

                "emails": emails,

                "application_links":
                    application_links

            }

        except Exception as error:

            self.log(
                f"Extraction error: {error}"
            )

            return {

                "page_url": url,
                "emails": [],
                "application_links": []

            }