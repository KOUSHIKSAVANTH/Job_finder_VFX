import os
import smtplib

from pathlib import Path
from email.message import EmailMessage


class EmailApplication:

    def __init__(self, profile):

        self.profile = profile

        self.sender = os.getenv(
            "JOB_FINDER_EMAIL"
        )

        self.password = os.getenv(
            "JOB_FINDER_APP_PASSWORD"
        )

    def send(
        self,
        recipient,
        company,
        role
    ):

        if not self.sender:
            raise RuntimeError(
                "JOB_FINDER_EMAIL missing."
            )

        if not self.password:
            raise RuntimeError(
                "JOB_FINDER_APP_PASSWORD missing."
            )

        message = EmailMessage()

        message["From"] = self.sender
        message["To"] = recipient

        message["Subject"] = (
            f"Application for {role}"
        )

        github = self.profile.get("github", "")
        portfolio = self.profile.get("portfolio_url", "")
        linkedin = self.profile.get("linkedin", "")
        name = self.profile.get("name", "")
        phone = self.profile.get("phone", "")

        message.set_content(
            f"""Hello,

I am applying for the {role} position at {company}.

I have attached my resume for your review.

Portfolio / Showreel: {portfolio}
LinkedIn: {linkedin}
GitHub: {github}

Thank you for your consideration.

Best regards,
{name}
{phone}
"""
        )

        resume = Path(
            self.profile["resume"]
        )

        if not resume.exists():

            raise FileNotFoundError(
                "Resume not found."
            )

        with open(resume, "rb") as file:

            message.add_attachment(
                file.read(),
                maintype="application",
                subtype="pdf",
                filename=resume.name
            )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as smtp:

            smtp.login(
                self.sender,
                self.password
            )

            smtp.send_message(
                message
            )