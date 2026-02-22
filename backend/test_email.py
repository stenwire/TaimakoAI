import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.services.email_service import EmailServiceFactory, EmailSchema
from app.core.config import settings

async def main():
    print(f"Testing email sending configuration...")
    print(f"SMTP_HOST: {settings.SMTP_HOST}")
    print(f"SMTP_PORT: {settings.SMTP_PORT}")
    print(f"SMTP_USER: {settings.SMTP_USER}")
    print(f"EMAILS_FROM_EMAIL: {settings.EMAILS_FROM_EMAIL}")
    
    email_service = EmailServiceFactory.get_service()
    
    recipient = "nwankwostephen039@yahoo.com"
    subject = "Test Email from Taimako AI"
    body = "This is a test email sent from the Taimako AI backend using Zoho Mail SMTP."
    html_body = "<h1>Test Email</h1><p>This is a test email sent from the <b>Taimako AI</b> backend using Zoho Mail SMTP.</p>"
    
    email = EmailSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        html_body=html_body
    )
    
    print(f"Sending email to {recipient}...")
    success = await email_service.send_email(email)
    
    if success:
        print("Email sent successfully!")
    else:
        print("Failed to send email.")

if __name__ == "__main__":
    asyncio.run(main())
