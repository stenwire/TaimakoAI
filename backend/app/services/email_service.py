from abc import ABC, abstractmethod
import logging
from typing import List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class EmailService(ABC):
    @abstractmethod
    def send_email(self, recipient_emails: List[str], subject: str, body: str) -> bool:
        """Sends an email to the specified recipients."""
        pass

class DummyEmailService(EmailService):
    def send_email(self, recipient_emails: List[str], subject: str, body: str) -> bool:
        """Simulates sending an email by logging the details."""
        try:
            logger.info("=== DUMMY EMAIL SERVICE ===")
            logger.info(f"Recipients: {', '.join(recipient_emails)}")
            logger.info(f"Subject: {subject}")
            logger.info("Body:")
            logger.info(body)
            logger.info("===========================")
            return True
        except Exception as e:
            logger.error(f"Failed to send dummy email: {e}")
            return False

class EmailServiceFactory:
    _service_instance: Optional[EmailService] = None

    @classmethod
    def get_service(cls, service_type: str = "dummy") -> EmailService:
        if cls._service_instance is None:
            if service_type == "dummy":
                cls._service_instance = DummyEmailService()
            # Future implementations (e.g., 'smtp', 'sendgrid') can be added here
            else:
                raise ValueError(f"Unknown service type: {service_type}")
        return cls._service_instance
