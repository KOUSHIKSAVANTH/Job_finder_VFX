from pathlib import Path


class GoogleFormsApplication:

    def __init__(
        self,
        page,
        profile,
        log=print
    ):

        self.page = page
        self.profile = profile
        self.log = log

    def get_answer(self, question):

        question = question.lower()

        answers = {
            "first name":
                self.profile["first_name"],

            "last name":
                self.profile["last_name"],

            "full name":
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

            "showreel":
                self.profile["portfolio_url"],

            "education":
                self.profile["education"],

            "experience":
                self.profile["experience"],

            "skills":
                self.profile["skills"]
        }

        for key in sorted(
            answers,
            key=len,
            reverse=True
        ):

            if key in question:
                return answers[key]

        return None

    def barrier_detected(self):

        text = self.page.locator(
            "body"
        ).inner_text().lower()

        for word in [
            "captcha",
            "recaptcha",
            "verify you are human"
        ]:

            if word in text:
                return word

        return None

    def fill_page(self):

        questions = self.page.locator(
            'div[role="listitem"]'
        )

        for index in range(
            questions.count()
        ):

            question = questions.nth(index)

            try:

                text = question.inner_text()

                answer = self.get_answer(
                    text
                )

                if not answer:
                    continue

                textarea = question.locator(
                    "textarea"
                )

                if textarea.count():

                    textarea.first.fill(answer)

                    continue

                inputs = question.locator(
                    'input[type="text"], '
                    'input[type="email"], '
                    'input[type="tel"], '
                    'input[type="url"]'
                )

                if inputs.count():

                    inputs.first.fill(answer)

            except Exception:
                continue

    def upload(self):

        resume = Path(
            self.profile["resume"]
        ).resolve()

        if not resume.exists():
            return

        fields = self.page.locator(
            'input[type="file"]'
        )

        for index in range(
            fields.count()
        ):

            try:

                fields.nth(
                    index
                ).set_input_files(
                    str(resume)
                )

            except Exception:
                continue

    def run(self):

        while True:

            barrier = self.barrier_detected()

            if barrier:

                return (
                    "Manual Required",
                    f"Barrier detected: {barrier}"
                )

            self.fill_page()

            self.upload()

            submit = self.page.get_by_text(
                "Submit",
                exact=True
            )

            if submit.count():

                submit.last.click()

                self.page.wait_for_timeout(
                    2000
                )

                return (
                    "Applied",
                    "Google Form submitted."
                )

            next_button = self.page.get_by_text(
                "Next",
                exact=True
            )

            if next_button.count():

                next_button.last.click()

                self.page.wait_for_timeout(
                    1000
                )

                continue

            return (
                "Manual Required",
                "Unsupported Google Form structure."
            )