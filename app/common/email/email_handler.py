from email.message import EmailMessage

from aiosmtplib import SMTP

from app.configs.config import configs


class EmailHandler:
    def __init__(self):
        self.smtp = SMTP(
            hostname=configs.EMAIL_HOSTNAME,
            port=configs.EMAIL_PORT,
            username=configs.EMAIL_HOST_USERNAME,
            password=configs.EMAIL_HOST_PASSWORD,
            use_tls=configs.EMAIL_USE_TLS
        )

    @staticmethod
    def _prepare_message(to: str, subject: str, body: str) -> EmailMessage:
        msg = EmailMessage()
        msg['From'] = configs.EMAIL_HOST_USERNAME
        msg['Subject'] = subject
        msg['To'] = to
        msg.set_content(body)
        return msg

    async def send_email(self, to: str, subject: str, body: str):
        msg = self._prepare_message(to, subject, body)
        async with self.smtp as smtp:
            await smtp.send_message(msg)
