"""Unit tests for the WhatsApp broadcast services."""
from datetime import datetime, timezone

import pytest

from app.models.whatsapp_broadcast import (
    CampaignAudienceType,
    CampaignStatus,
    TemplateStatus,
    WhatsAppCampaignMessage,
    WhatsAppContact,
    WhatsAppTemplate,
)
from app.services.whatsapp import campaigns as campaign_service
from app.services.whatsapp import contacts as contact_service
from app.services.whatsapp import templates as template_service


# ---------- templates.extract_variables ----------


@pytest.mark.unit
class TestExtractVariables:
    def test_extracts_ordered_unique(self):
        body = "Hi {{1}}, your order {{2}} is ready. Thanks {{1}}!"
        assert template_service.extract_variables(body) == ["1", "2"]

    def test_empty_body(self):
        assert template_service.extract_variables("") == []

    def test_no_variables(self):
        assert template_service.extract_variables("Hello world") == []

    def test_with_whitespace(self):
        assert template_service.extract_variables("Hi {{ 1 }} and {{ 2 }}") == ["1", "2"]


# ---------- contacts.normalize_phone ----------


@pytest.mark.unit
class TestNormalizePhone:
    def test_valid_e164_passes(self):
        assert contact_service.normalize_phone("+2348012345678") == "+2348012345678"

    def test_adds_plus_prefix(self):
        assert contact_service.normalize_phone("2348012345678") == "+2348012345678"

    def test_strips_whitespace_and_punct(self):
        assert contact_service.normalize_phone("+234 (801) 234-5678") == "+2348012345678"

    def test_rejects_short_numbers(self):
        assert contact_service.normalize_phone("+123") is None

    def test_rejects_empty(self):
        assert contact_service.normalize_phone("") is None
        assert contact_service.normalize_phone(None) is None


# ---------- contacts.import_csv ----------


@pytest.mark.unit
class TestImportCsv:
    def test_happy_path(self, db_session, auth_client_with_business):
        _, _, business = auth_client_with_business
        csv = b"phone,name,tags\n+2348012345678,Alice,vip\n+2347098765432,Bob,\n"
        result = contact_service.import_csv(db_session, business.id, csv)
        assert result.imported == 2
        assert result.skipped == 0
        contacts = db_session.query(WhatsAppContact).filter_by(business_id=business.id).all()
        assert {c.phone_e164 for c in contacts} == {"+2348012345678", "+2347098765432"}

    def test_rejects_missing_header(self, db_session, auth_client_with_business):
        _, _, business = auth_client_with_business
        result = contact_service.import_csv(db_session, business.id, b"wrong,headers\nfoo,bar")
        assert result.imported == 0
        assert any("phone" in e for e in result.errors)

    def test_skips_invalid_phones(self, db_session, auth_client_with_business):
        _, _, business = auth_client_with_business
        csv = b"phone,name\n+2348012345678,Good\nbad,Bad\n"
        result = contact_service.import_csv(db_session, business.id, csv)
        assert result.imported == 1
        assert result.skipped == 1

    def test_deduplicates_within_business(self, db_session, auth_client_with_business):
        _, _, business = auth_client_with_business
        csv1 = b"phone,name\n+2348012345678,Alice\n"
        contact_service.import_csv(db_session, business.id, csv1)
        csv2 = b"phone,name\n+2348012345678,Alice2\n"
        result = contact_service.import_csv(db_session, business.id, csv2)
        assert result.imported == 0
        assert result.skipped == 1


# ---------- campaigns.create_campaign ----------


def _approved_template(db_session, business_id: str) -> WhatsAppTemplate:
    template = WhatsAppTemplate(
        business_id=business_id,
        name="promo",
        category="MARKETING",
        language="en_US",
        body_text="Hi {{1}}, check this out!",
        variables=["1"],
        status=TemplateStatus.APPROVED.value,
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.mark.unit
class TestCreateCampaign:
    def test_rejects_non_approved_template(self, db_session, auth_client_with_business):
        _, user, business = auth_client_with_business
        template = WhatsAppTemplate(
            business_id=business.id,
            name="draft",
            category="MARKETING",
            language="en_US",
            body_text="hi",
            status=TemplateStatus.DRAFT.value,
        )
        db_session.add(template)
        db_session.commit()
        with pytest.raises(ValueError, match="APPROVED"):
            campaign_service.create_campaign(
                db_session,
                business.id,
                name="c1",
                template_id=template.id,
                audience_type=CampaignAudienceType.ADHOC.value,
                audience_ref={"phones": ["+2348012345678"]},
                variable_mapping={"1": {"type": "literal", "value": "Alice"}},
                created_by_user_id=user.id,
            )

    def test_adhoc_audience_expansion(self, db_session, auth_client_with_business):
        _, user, business = auth_client_with_business
        template = _approved_template(db_session, business.id)
        campaign = campaign_service.create_campaign(
            db_session,
            business.id,
            name="c1",
            template_id=template.id,
            audience_type=CampaignAudienceType.ADHOC.value,
            audience_ref={"phones": ["+2348012345678", "+2347098765432", "bad"]},
            variable_mapping={"1": {"type": "literal", "value": "Friend"}},
            created_by_user_id=user.id,
        )
        assert campaign.total_recipients == 2
        msgs = (
            db_session.query(WhatsAppCampaignMessage)
            .filter_by(campaign_id=campaign.id)
            .all()
        )
        assert {m.contact_phone for m in msgs} == {"+2348012345678", "+2347098765432"}
        assert all(m.variables_snapshot == {"1": "Friend"} for m in msgs)

    def test_list_audience_expansion(self, db_session, auth_client_with_business):
        _, user, business = auth_client_with_business
        template = _approved_template(db_session, business.id)

        c1 = contact_service.create_contact(
            db_session, business.id, phone="+2348012345678", name="Alice"
        )
        c2 = contact_service.create_contact(
            db_session, business.id, phone="+2347098765432", name="Bob"
        )
        lst = contact_service.create_list(db_session, business.id, name="VIPs")
        contact_service.add_members(db_session, lst, [c1.id, c2.id])

        campaign = campaign_service.create_campaign(
            db_session,
            business.id,
            name="c2",
            template_id=template.id,
            audience_type=CampaignAudienceType.LIST.value,
            audience_ref={"list_id": lst.id},
            variable_mapping={"1": {"type": "field", "field": "name"}},
            created_by_user_id=user.id,
        )
        assert campaign.total_recipients == 2
        msgs = {
            m.contact_phone: m.variables_snapshot
            for m in db_session.query(WhatsAppCampaignMessage)
            .filter_by(campaign_id=campaign.id)
            .all()
        }
        assert msgs["+2348012345678"] == {"1": "Alice"}
        assert msgs["+2347098765432"] == {"1": "Bob"}


# ---------- campaigns.schedule / cancel ----------


@pytest.mark.unit
class TestScheduleCancel:
    def test_cannot_cancel_completed(self, db_session, auth_client_with_business):
        _, user, business = auth_client_with_business
        template = _approved_template(db_session, business.id)
        campaign = campaign_service.create_campaign(
            db_session,
            business.id,
            name="c",
            template_id=template.id,
            audience_type=CampaignAudienceType.ADHOC.value,
            audience_ref={"phones": ["+2348012345678"]},
            variable_mapping={"1": {"type": "literal", "value": "x"}},
            created_by_user_id=user.id,
        )
        campaign.status = CampaignStatus.COMPLETED.value
        db_session.commit()
        with pytest.raises(ValueError):
            campaign_service.cancel_campaign(db_session, campaign)

    def test_schedule_flips_status_and_sets_time(self, db_session, auth_client_with_business):
        _, user, business = auth_client_with_business
        template = _approved_template(db_session, business.id)
        campaign = campaign_service.create_campaign(
            db_session,
            business.id,
            name="c",
            template_id=template.id,
            audience_type=CampaignAudienceType.ADHOC.value,
            audience_ref={"phones": ["+2348012345678"]},
            variable_mapping={"1": {"type": "literal", "value": "x"}},
            created_by_user_id=user.id,
        )
        scheduled_at = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
        campaign = campaign_service.schedule_campaign(db_session, campaign, scheduled_at)
        assert campaign.status == CampaignStatus.SCHEDULED.value
        # SQLite strips tz; compare naive values
        assert campaign.scheduled_at.replace(tzinfo=None) == scheduled_at.replace(tzinfo=None)
