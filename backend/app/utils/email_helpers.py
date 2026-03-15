"""
Subscription email notification helpers.

Uses the existing EmailServiceFactory (DummyEmailService in dev, SMTPEmailService in production).
All functions are async to match the EmailService.send_email signature.
"""
import logging
from app.services.email_service import EmailSchema, EmailServiceFactory

logger = logging.getLogger(__name__)


async def send_subscription_created_email(email: str, plan_name: str) -> bool:
    """Notify user that their subscription has been created successfully."""
    service = EmailServiceFactory.get_service()
    schema = EmailSchema(
        subject="Welcome! Your Subscription is Active",
        recipients=[email],
        body=(
            f"Your {plan_name} subscription is now active.\n\n"
            f"You now have access to all {plan_name} tier features. "
            f"Your credits have been provisioned and you're ready to go.\n\n"
            f"Thank you for choosing Taimako AI!"
        ),
        html_body=(
            f"<h2>Welcome! Your Subscription is Active</h2>"
            f"<p>Your <strong>{plan_name}</strong> subscription is now active.</p>"
            f"<p>You now have access to all {plan_name} tier features. "
            f"Your credits have been provisioned and you're ready to go.</p>"
            f"<p>Thank you for choosing Taimako AI!</p>"
        )
    )
    result = await service.send_email(schema)
    if result:
        logger.info(f"Subscription created email sent to {email}")
    return result


async def send_subscription_cancelled_email(email: str) -> bool:
    """Notify user that their subscription has been cancelled."""
    service = EmailServiceFactory.get_service()
    schema = EmailSchema(
        subject="Your Subscription Has Been Cancelled",
        recipients=[email],
        body=(
            "Your subscription has been cancelled.\n\n"
            "You will continue to have access until the end of your current billing period. "
            "After that, your account will revert to the free tier.\n\n"
            "If this was a mistake, you can re-subscribe at any time from your settings."
        ),
        html_body=(
            "<h2>Your Subscription Has Been Cancelled</h2>"
            "<p>Your subscription has been cancelled.</p>"
            "<p>You will continue to have access until the end of your current billing period. "
            "After that, your account will revert to the free tier.</p>"
            "<p>If this was a mistake, you can re-subscribe at any time from your settings.</p>"
        )
    )
    result = await service.send_email(schema)
    if result:
        logger.info(f"Subscription cancelled email sent to {email}")
    return result


async def send_payment_success_email(email: str, plan_name: str, amount: int) -> bool:
    """Notify user of a successful payment (initial or renewal)."""
    # Amount is in minor units (kobo), convert to major units for display
    amount_display = f"₦{amount / 100:,.2f}" if amount else "N/A"

    service = EmailServiceFactory.get_service()
    schema = EmailSchema(
        subject="Payment Received Successfully",
        recipients=[email],
        body=(
            f"We've received your payment of {amount_display} for the {plan_name} plan.\n\n"
            f"Your subscription remains active and your credits have been refreshed.\n\n"
            f"Thank you for your continued support!"
        ),
        html_body=(
            f"<h2>Payment Received Successfully</h2>"
            f"<p>We've received your payment of <strong>{amount_display}</strong> "
            f"for the <strong>{plan_name}</strong> plan.</p>"
            f"<p>Your subscription remains active and your credits have been refreshed.</p>"
            f"<p>Thank you for your continued support!</p>"
        )
    )
    result = await service.send_email(schema)
    if result:
        logger.info(f"Payment success email sent to {email}")
    return result


async def send_payment_failed_email(email: str, plan_name: str) -> bool:
    """Notify user that a renewal payment failed and action is needed."""
    service = EmailServiceFactory.get_service()
    schema = EmailSchema(
        subject="Action Required: Payment Failed",
        recipients=[email],
        body=(
            f"We were unable to process your renewal payment for the {plan_name} plan.\n\n"
            f"Please update your payment method to avoid service interruption. "
            f"You can do this from your subscription settings.\n\n"
            f"If you need assistance, please contact our support team."
        ),
        html_body=(
            f"<h2>Action Required: Payment Failed</h2>"
            f"<p>We were unable to process your renewal payment for the "
            f"<strong>{plan_name}</strong> plan.</p>"
            f"<p>Please update your payment method to avoid service interruption. "
            f"You can do this from your subscription settings.</p>"
            f"<p>If you need assistance, please contact our support team.</p>"
        )
    )
    result = await service.send_email(schema)
    if result:
        logger.info(f"Payment failed email sent to {email}")
    return result


async def send_plan_upgraded_email(email: str, old_plan: str, new_plan: str) -> bool:
    """Notify user that their plan has been upgraded."""
    service = EmailServiceFactory.get_service()
    schema = EmailSchema(
        subject=f"Plan Upgraded: {old_plan.capitalize()} → {new_plan.capitalize()}",
        recipients=[email],
        body=(
            f"Your plan has been upgraded from {old_plan.capitalize()} to {new_plan.capitalize()}.\n\n"
            f"Your new {new_plan.capitalize()} tier features and credits are now active.\n\n"
            f"Enjoy the upgrade!"
        ),
        html_body=(
            f"<h2>Plan Upgraded Successfully!</h2>"
            f"<p>Your plan has been upgraded from <strong>{old_plan.capitalize()}</strong> "
            f"to <strong>{new_plan.capitalize()}</strong>.</p>"
            f"<p>Your new {new_plan.capitalize()} tier features and credits are now active.</p>"
            f"<p>Enjoy the upgrade!</p>"
        )
    )
    result = await service.send_email(schema)
    if result:
        logger.info(f"Plan upgraded email sent to {email}")
    return result
