from abc import ABC, abstractmethod
import logging
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import aiosmtplib
from email.message import EmailMessage

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class EmailSchema(BaseModel):
    subject: str
    recipients: List[EmailStr]
    body: str
    html_body: Optional[str] = None

class EmailService(ABC):
    @abstractmethod
    async def send_email(self, email: EmailSchema) -> bool:
        """Sends an email to the specified recipients."""
        pass

class DummyEmailService(EmailService):
    async def send_email(self, email: EmailSchema) -> bool:
        """Simulates sending an email by logging the details."""
        try:
            logger.info("=== DUMMY EMAIL SERVICE ===")
            logger.info(f"Recipients: {', '.join(email.recipients)}")
            logger.info(f"Subject: {email.subject}")
            logger.info("Body:")
            logger.info(email.body)
            if email.html_body:
                logger.info("HTML Body present")
            logger.info("===========================")
            return True
        except Exception as e:
            logger.error(f"Failed to send dummy email: {e}")
            return False

class SMTPEmailService(EmailService):
    async def send_email(self, email: EmailSchema) -> bool:
        """Sends an email using SMTP."""
        message = EmailMessage()
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        message["To"] = ", ".join(email.recipients)
        message["Subject"] = email.subject
        message.set_content(email.body)

        if email.html_body:
            message.add_alternative(email.html_body, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True, # ZOHO usually requires TLS/STARTTLS
            )
            logger.info(f"Email sent successfully to {email.recipients}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False

class EmailServiceFactory:
    _service_instance: Optional[EmailService] = None

    @classmethod
    def get_service(cls) -> EmailService:
        if cls._service_instance is None:
            if settings.SMTP_HOST and settings.SMTP_USER:
                 cls._service_instance = SMTPEmailService()
            else:
                logger.warning("SMTP not configured, using DummyEmailService")
                cls._service_instance = DummyEmailService()
                
        return cls._service_instance
