from src.infrastructure.celery_worker.celery_app import celery_app
from src.infrastructure.email_handler import EmailHandler


@celery_app.task
def send_otp_code_email(email: str, otp_code: str):
    content = f"Your verification code is {otp_code}"
    subject = "Welcome to FastAuth"
    EmailHandler().send_email(email, subject, content)
