from email.message import EmailMessage
from smtplib import SMTP_SSL, SMTPException

from src.core import configs


class EmailHandler:
    @staticmethod
    def _login(smtp):
        try:
            smtp.login(
                user=configs.EMAIL_HOST_USERNAME,
                password=configs.EMAIL_HOST_PASSWORD
            )
        except SMTPException:
            pass
            # add logger

    @staticmethod
    def _prepare_message(to: str, subject: str, body: str) -> EmailMessage:
        msg = EmailMessage()
        msg['From'] = configs.EMAIL_HOST_USERNAME
        msg['Subject'] = subject
        msg['To'] = to
        msg.set_content(body)
        return msg

    def send_email(self, to: str, subject: str, body: str):
        msg = self._prepare_message(to, subject, body)
        smtp = SMTP_SSL(host=configs.EMAIL_HOSTNAME, port=configs.EMAIL_PORT)
        with smtp as smtp:
            self._login(smtp)
            smtp.send_message(msg)
