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
        log=print,
        auto_submit=False
    ):

        self.browser = browser
        self.profile = profile
        self.log = log
        self.auto_submit = auto_submit

    def _select_email(
        self,
        emails,
        allow_personal=False
    ):

        application_signals = [
            "apply",
            "career",
            "hiring",
            "recruit",
            "job"
        ]

        blocked_signals = [
            "admin",
            "info",
            "privacy",
            "support",
            "noreply",
            "no-reply",
            " webmaster"
        ]

        for email in emails:
            normalized = email.lower()

            if any(
                signal in normalized
                for signal in blocked_signals
            ):
                continue

            if any(
                signal in normalized
                for signal in application_signals
            ) or allow_personal:
                return email

        return None

    def apply(
        self,
        url,
        company,
        role,
        emails=None,
        application_links=None,
        post_emails=None,
        linkedin_post=False
    ):

        emails = emails or []
        application_links = application_links or []
        post_emails = post_emails or []

        if not self.auto_submit:
            return (
                "Manual Required",
                "Automatic submission is disabled."
            )

        post_email = self._select_email(
            post_emails,
            allow_personal=True
        ) if linkedin_post else None

        has_application_link = bool(
            application_links
        ) and not post_email

        application_url = (
            application_links[0]
            if has_application_link
            else url
        )

        if post_email:
            email = post_email
        elif not has_application_link:
            email = self._select_email(emails)
        else:
            email = None

        if email:
            try:
                EmailApplication(
                    self.profile
                ).send(
                    email,
                    company,
                    role
                )

                return (
                    "Sent",
                    f"Resume emailed to {email}"
                )

            except Exception as error:
                return (
                    "Failed",
                    str(error)
                )

        if "docs.google.com/forms" in application_url:
            page = self.browser.open(application_url)

            return GoogleFormsApplication(
                page,
                self.profile,
                self.log
            ).run()

        page = self.browser.open(application_url)

        return WebsiteApplication(
            page,
            self.profile,
            self.log
        ).run()