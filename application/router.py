from application.google_forms import (
    GoogleFormsApplication
)

from application.website import (
    WebsiteApplication
)

from application.email_sender import (
    EmailApplication
)


class ApplicationRouter:

    def __init__(
        self,
        browser,
        profile,
        log=print
    ):

        self.browser = browser
        self.profile = profile
        self.log = log

    def apply(
        self,
        url,
        company,
        role,
        emails=None
    ):

        emails = emails or []

        # Direct Google Form
        if "docs.google.com/forms" in url:

            page = self.browser.open(url)

            automation = (
                GoogleFormsApplication(
                    page,
                    self.profile,
                    self.log
                )
            )

            return automation.run()

        # If the job specifically exposes
        # a contact email, send automatically.
        if emails:

            try:

                EmailApplication(
                    self.profile
                ).send(
                    emails[0],
                    company,
                    role
                )

                return (
                    "Sent",
                    f"Resume emailed to {emails[0]}"
                )

            except Exception as error:

                return (
                    "Failed",
                    str(error)
                )

        # General website
        page = self.browser.open(url)

        automation = WebsiteApplication(
            page,
            self.profile,
            self.log
        )

        return automation.run()