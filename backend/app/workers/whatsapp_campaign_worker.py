"""Standalone worker that executes scheduled WhatsApp broadcast campaigns.

Run as: `uv run python -m app.workers.whatsapp_campaign_worker`

The worker polls `whatsapp_campaigns` for SCHEDULED rows whose
`scheduled_at` has elapsed, claims them via `FOR UPDATE SKIP LOCKED`
so multiple replicas don't double-send, then invokes
`app.services.whatsapp.campaigns.execute_campaign` to send messages.
"""
import asyncio
import signal
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

# Import all models so SQLAlchemy can resolve string-based relationships
# (this worker runs standalone, not through FastAPI/main.py).
from app.models.user import User  # noqa: F401
from app.models.business import Business  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.payment import PaymentTransaction  # noqa: F401
from app.models.widget import WidgetSettings, GuestUser, GuestMessage  # noqa: F401
from app.models.chat_session import ChatSession  # noqa: F401
from app.models.escalation import Escalation  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.analytics import AnalyticsDailySummary  # noqa: F401
from app.models.whatsapp_broadcast import CampaignStatus, WhatsAppCampaign
from app.services.whatsapp import campaigns as campaign_service

POLL_INTERVAL = settings.WHATSAPP_CAMPAIGN_POLL_INTERVAL_SECONDS
DEFAULT_RATE = settings.WHATSAPP_CAMPAIGN_SEND_RATE_PER_SECOND
CLAIM_LIMIT = 5


def _resolve_rate_for_campaign(db, campaign: WhatsAppCampaign) -> int:
    """Per-business override on widget_settings, else env default."""
    business = db.query(Business).filter(Business.id == campaign.business_id).first()
    if not business:
        return DEFAULT_RATE
    widget = (
        db.query(WidgetSettings)
        .filter(WidgetSettings.user_id == business.user_id)
        .first()
    )
    if widget and widget.whatsapp_send_rate_per_second:
        return widget.whatsapp_send_rate_per_second
    return DEFAULT_RATE


class WorkerShutdown(Exception):
    pass


_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    print(f"whatsapp-worker: signal {signum} received; shutting down after current batch")
    _shutdown = True


def _recover_orphaned_campaigns() -> None:
    """On startup, revert any SENDING rows back to SCHEDULED so they resume."""
    db = SessionLocal()
    try:
        stale = (
            db.query(WhatsAppCampaign)
            .filter(WhatsAppCampaign.status == CampaignStatus.SENDING.value)
            .all()
        )
        for c in stale:
            c.status = CampaignStatus.SCHEDULED.value
            c.started_at = None
        if stale:
            db.commit()
            print(f"whatsapp-worker: recovered {len(stale)} orphaned campaign(s)")
    finally:
        db.close()


def _claim_due_campaigns() -> list[str]:
    """Atomically claim up to CLAIM_LIMIT due campaigns via row locking.

    Returns campaign IDs. The lock is released when the transaction
    commits (we flip status to SENDING in the same tx so other workers
    skip these rows).
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Use raw SQL for FOR UPDATE SKIP LOCKED (portable-ish; PostgreSQL required in prod).
        result = db.execute(
            text(
                """
                SELECT id FROM whatsapp_campaigns
                WHERE status = :scheduled
                  AND scheduled_at <= :now
                ORDER BY scheduled_at ASC
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
                """
            ),
            {
                "scheduled": CampaignStatus.SCHEDULED.value,
                "now": now,
                "limit": CLAIM_LIMIT,
            },
        )
        ids = [row[0] for row in result]
        if not ids:
            db.commit()
            return []

        # Mark as SENDING inside the same transaction while the lock is held.
        db.execute(
            text(
                """
                UPDATE whatsapp_campaigns
                SET status = :sending, started_at = :now, updated_at = :now
                WHERE id = ANY(:ids)
                """
            ),
            {
                "sending": CampaignStatus.SENDING.value,
                "now": now,
                "ids": ids,
            },
        )
        db.commit()
        return ids
    except Exception as e:
        db.rollback()
        print(f"whatsapp-worker: claim error: {e}")
        return []
    finally:
        db.close()


async def _run_campaign(campaign_id: str) -> None:
    db = SessionLocal()
    try:
        campaign = (
            db.query(WhatsAppCampaign).filter(WhatsAppCampaign.id == campaign_id).first()
        )
        if not campaign:
            return
        try:
            rate = _resolve_rate_for_campaign(db, campaign)
            await campaign_service.execute_campaign(db, campaign, rate_per_second=rate)
        except Exception as e:
            print(f"whatsapp-worker: campaign {campaign_id} failed: {e}")
            campaign.status = CampaignStatus.FAILED.value
            campaign.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


async def main() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    _recover_orphaned_campaigns()
    print(
        f"whatsapp-worker: started "
        f"(poll={POLL_INTERVAL}s, default_rate={DEFAULT_RATE}/s, claim_limit={CLAIM_LIMIT})"
    )

    while not _shutdown:
        ids = _claim_due_campaigns()
        if ids:
            print(f"whatsapp-worker: claimed {len(ids)} campaign(s): {ids}")
            await asyncio.gather(*[_run_campaign(cid) for cid in ids])
        else:
            await asyncio.sleep(POLL_INTERVAL)

    print("whatsapp-worker: stopped")


if __name__ == "__main__":
    asyncio.run(main())
