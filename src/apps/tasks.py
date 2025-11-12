from src.infrastructure.celery_app import celery_app
from src.infrastructure.email_handler import EmailHandler


@celery_app.task(bind=True)
def send_otp_code_email(self, email: str, otp_code: str):
    content = f"Your verification code is {otp_code}"
    subject = "Welcome to FastAuth"
    try:
        EmailHandler().send_email(email, subject, content)
    except Exception as e:
        self.retry(exc=e, max_retries=3, countdown=10)
