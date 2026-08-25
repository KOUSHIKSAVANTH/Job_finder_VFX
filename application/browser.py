from playwright.sync_api import (
    sync_playwright
)


class Browser:

    def __init__(self):

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):

        if self.page:
            return self.page

        self.playwright = (
            sync_playwright().start()
        )

        self.browser = (
            self.playwright.chromium.launch(
                headless=False
            )
        )

        self.context = (
            self.browser.new_context()
        )

        self.page = (
            self.context.new_page()
        )

        return self.page

    def open(self, url):

        self.start()

        self.page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        return self.page

    def close(self):

        if self.browser:
            self.browser.close()

        if self.playwright:
            self.playwright.stop()