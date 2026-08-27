from pathlib import Path


class WebsiteApplication:

    def __init__(
        self,
        page,
        profile,
        log=print
    ):

        self.page = page
        self.profile = profile
        self.log = log

    def barrier(self):

        text = self.page.locator(
            "body"
        ).inner_text().lower()

        if "captcha" in text:
            return "CAPTCHA"

        if self.page.locator(
            'input[type="password"]'
        ).count():
            return "Login required"

        return None

    def get_value(self, description):

        description = description.lower()

        fields = {
            "first name":
                self.profile["first_name"],

            "last name":
                self.profile["last_name"],

            "full name":
                self.profile["name"],

            "name":
                self.profile["name"],

            "email":
                self.profile["email"],

            "phone":
                self.profile["phone"],

            "mobile":
                self.profile["phone"],

            "location":
                self.profile["location"],

            "linkedin":
                self.profile["linkedin"],

            "github":
                self.profile["github"],

            "portfolio":
                self.profile["portfolio_url"],

            "website":
                self.profile["portfolio_url"],

            "skills":
                self.profile["skills"],

            "education":
                self.profile["education"],

            "experience":
                self.profile["experience"]
        }

        for key in sorted(
            fields,
            key=len,
            reverse=True
        ):

            if key in description:
                return fields[key]

        return None

    def fill(self):

        elements = self.page.locator(
            "input, textarea"
        )

        for index in range(
            elements.count()
        ):

            field = elements.nth(index)

            try:

                field_type = (
                    field.get_attribute("type")
                    or "text"
                )

                if field_type in [
                    "hidden",
                    "file",
                    "submit",
                    "checkbox",
                    "radio",
                    "password"
                ]:
                    continue

                description = " ".join([
                    field.get_attribute("name") or "",
                    field.get_attribute(
                        "placeholder"
                    ) or "",
                    field.get_attribute(
                        "aria-label"
                    ) or "",
                    field.get_attribute("id") or ""
                ])

                value = self.get_value(
                    description
                )

                if value and field.is_visible():

                    field.fill(value)

            except Exception:
                continue

    def upload(self):

        resume = Path(
            self.profile["resume"]
        ).resolve()

        if not resume.exists():
            return

        files = self.page.locator(
            'input[type="file"]'
        )

        for index in range(
            files.count()
        ):

            try:

                files.nth(index).set_input_files(
                    str(resume)
                )

            except Exception:
                continue

    def submit(self):

        selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Apply")',
            'button:has-text("Submit Application")',
            'button:has-text("Submit")'
        ]

        for selector in selectors:

            try:

                button = self.page.locator(
                    selector
                ).first

                if (
                    button.count()
                    and button.is_visible()
                    and button.is_enabled()
                ):

                    button.click()

                    return True

            except Exception:
                continue

        return False

    def submission_confirmed(self, previous_url):

        try:
            current_url = self.page.url

            if current_url != previous_url:
                return True

            text = self.page.locator(
                "body"
            ).inner_text().lower()

            return any(
                phrase in text
                for phrase in [
                    "thank you",
                    "application received",
                    "application submitted",
                    "successfully submitted",
                    "confirmation"
                ]
            )

        except Exception:
            return False

    def run(self):

        barrier = self.barrier()

        if barrier:

            return (
                "Manual Required",
                barrier
            )

        self.fill()

        self.upload()

        previous_url = self.page.url

        if self.submit():

            self.page.wait_for_timeout(
                1500
            )

            if not self.submission_confirmed(
                previous_url
            ):
                return (
                    "Manual Required",
                    "Submission was not confirmed."
                )

            return (
                "Applied",
                "Website form submitted."
            )

        return (
            "Manual Required",
            "Could not safely identify application flow."
        )