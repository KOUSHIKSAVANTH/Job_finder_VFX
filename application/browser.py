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

        # Reuse the existing browser only if
        # it is still connected.
        if (
            self.browser
            and self.browser.is_connected()
            and self.page
            and not self.page.is_closed()
        ):

            return self.page

        # Reset closed objects before starting again.
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

        page = self.start()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        return page


    def close(self):

        try:

            if (
                self.context
                and not self.context.pages == []
            ):

                self.context.close()

        except Exception:

            pass


        try:

            if (
                self.browser
                and self.browser.is_connected()
            ):

                self.browser.close()

        except Exception:

            pass


        try:

            if self.playwright:

                self.playwright.stop()

        except Exception:

            pass


        # IMPORTANT:
        # Forget all closed Playwright objects.
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None