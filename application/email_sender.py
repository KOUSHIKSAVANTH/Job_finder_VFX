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

        message.set_content(
            f"""Hello,

I am applying for the {role} position at {company}.

Please find my resume attached.

Portfolio / Showreel:
{self.profile["portfolio_url"]}

LinkedIn:
{self.profile["linkedin"]}

Thank you for your consideration.

Best regards,
{self.profile["name"]}
{self.profile["phone"]}
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