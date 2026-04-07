from sqladmin import ModelView

from app.models.user import User
from app.models.business import Business
from app.models.plan import Plan
from app.models.payment import PaymentTransaction
from app.models.chat_session import ChatSession
from app.models.widget import WidgetSettings, GuestUser, GuestMessage
from app.models.escalation import Escalation
from app.models.document import Document
from app.models.analytics import AnalyticsDailySummary


# ─── Users & Auth ────────────────────────────────────────────────────────────

class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    category = "Users & Auth"

    column_list = [User.id, User.email, User.name, User.is_active, User.is_admin, User.created_at]
    column_details_exclude_list = [User.hashed_password]
    column_searchable_list = [User.email, User.name]
    column_sortable_list = [User.email, User.name, User.is_active, User.is_admin, User.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = [User.hashed_password, User.created_at, User.updated_at]

    column_labels = {
        "id": "ID",
        "google_id": "Google ID",
        "is_active": "Active",
        "is_admin": "Admin",
        "created_at": "Created",
        "updated_at": "Updated",
    }

    can_export = True
    export_max_rows = 1000


# ─── Business ────────────────────────────────────────────────────────────────

class BusinessAdmin(ModelView, model=Business):
    name = "Business"
    name_plural = "Businesses"
    icon = "fa-solid fa-building"
    category = "Business"

    column_list = [
        Business.id, Business.business_name, Business.user_id,
        Business.subscription_tier, Business.subscription_status,
        Business.allocated_ai_responses, Business.used_ai_responses,
        Business.created_at,
    ]
    column_details_exclude_list = [Business.authorization_code, Business.subscription_email_token]
    column_searchable_list = [Business.business_name, Business.user_id, Business.website]
    column_sortable_list = [
        Business.business_name, Business.subscription_tier,
        Business.subscription_status, Business.created_at,
    ]
    column_default_sort = ("created_at", True)

    form_excluded_columns = [
        Business.authorization_code, Business.subscription_email_token,
        Business.created_at, Business.updated_at,
    ]

    column_labels = {
        "user_id": "Owner ID",
        "subscription_tier": "Tier",
        "subscription_status": "Sub Status",
        "allocated_ai_responses": "AI Credits",
        "used_ai_responses": "AI Used",
        "allocated_escalations": "Esc. Credits",
        "used_escalations": "Esc. Used",
        "payment_provider": "Provider",
    }

    can_export = True


class PlanAdmin(ModelView, model=Plan):
    name = "Plan"
    name_plural = "Plans"
    icon = "fa-solid fa-tags"
    category = "Business"

    column_list = [Plan.id, Plan.name, Plan.plan_code, Plan.price, Plan.currency, Plan.interval, Plan.tier, Plan.is_active]
    column_searchable_list = [Plan.name, Plan.plan_code]
    column_sortable_list = [Plan.name, Plan.price, Plan.tier, Plan.is_active]
    column_default_sort = ("tier", False)

    form_include_pk = True
    form_excluded_columns = [Plan.created_at, Plan.updated_at]

    column_labels = {"plan_code": "Code", "is_active": "Active"}

    can_export = True


# ─── Payments ────────────────────────────────────────────────────────────────

class PaymentTransactionAdmin(ModelView, model=PaymentTransaction):
    name = "Transaction"
    name_plural = "Transactions"
    icon = "fa-solid fa-credit-card"
    category = "Payments"

    column_list = [
        PaymentTransaction.id, PaymentTransaction.business_id,
        PaymentTransaction.amount, PaymentTransaction.currency,
        PaymentTransaction.status, PaymentTransaction.provider,
        PaymentTransaction.transaction_type, PaymentTransaction.created_at,
    ]
    column_details_exclude_list = [PaymentTransaction.raw_webhook_payload]
    column_searchable_list = [PaymentTransaction.reference, PaymentTransaction.business_id, PaymentTransaction.status]
    column_sortable_list = [
        PaymentTransaction.amount, PaymentTransaction.status,
        PaymentTransaction.created_at, PaymentTransaction.provider,
    ]
    column_default_sort = ("created_at", True)

    can_create = False
    can_edit = False
    can_delete = False

    column_labels = {"business_id": "Business", "transaction_type": "Type"}

    can_export = True


# ─── Chat & Messaging ───────────────────────────────────────────────────────

class ChatSessionAdmin(ModelView, model=ChatSession):
    name = "Chat Session"
    name_plural = "Chat Sessions"
    icon = "fa-solid fa-comments"
    category = "Chat & Messaging"

    column_list = [
        ChatSession.id, ChatSession.guest_id, ChatSession.channel,
        ChatSession.is_active, ChatSession.total_messages,
        ChatSession.session_duration, ChatSession.created_at,
    ]
    column_searchable_list = [ChatSession.guest_id, ChatSession.channel, ChatSession.top_intent, ChatSession.country]
    column_sortable_list = [
        ChatSession.created_at, ChatSession.is_active,
        ChatSession.total_messages, ChatSession.session_duration, ChatSession.channel,
    ]
    column_default_sort = ("created_at", True)

    can_create = False
    form_excluded_columns = [ChatSession.created_at, ChatSession.last_message_at]

    column_labels = {
        "guest_id": "Guest",
        "session_duration": "Duration (s)",
        "total_messages": "Messages",
        "user_messages": "User Msgs",
        "ai_messages": "AI Msgs",
        "first_response_time": "1st Response (s)",
    }

    can_export = True


class GuestMessageAdmin(ModelView, model=GuestMessage):
    name = "Message"
    name_plural = "Messages"
    icon = "fa-solid fa-envelope"
    category = "Chat & Messaging"

    column_list = [
        GuestMessage.id, GuestMessage.guest_id, GuestMessage.session_id,
        GuestMessage.sender, GuestMessage.created_at,
    ]
    column_details_list = [
        GuestMessage.id, GuestMessage.guest_id, GuestMessage.session_id,
        GuestMessage.sender, GuestMessage.message_text, GuestMessage.created_at,
    ]
    column_searchable_list = [GuestMessage.guest_id, GuestMessage.session_id, GuestMessage.sender]
    column_sortable_list = [GuestMessage.created_at, GuestMessage.sender]
    column_default_sort = ("created_at", True)

    can_create = False
    can_edit = False
    can_delete = False

    column_labels = {"guest_id": "Guest", "session_id": "Session", "message_text": "Message"}

    can_export = True


class EscalationAdmin(ModelView, model=Escalation):
    name = "Escalation"
    name_plural = "Escalations"
    icon = "fa-solid fa-triangle-exclamation"
    category = "Chat & Messaging"

    column_list = [
        Escalation.id, Escalation.business_id, Escalation.session_id,
        Escalation.status, Escalation.sentiment, Escalation.created_at,
    ]
    column_searchable_list = [Escalation.business_id, Escalation.status, Escalation.sentiment]
    column_sortable_list = [Escalation.status, Escalation.created_at, Escalation.sentiment]
    column_default_sort = ("created_at", True)

    can_create = False
    form_excluded_columns = [Escalation.created_at, Escalation.updated_at]

    column_labels = {"business_id": "Business", "session_id": "Session"}

    can_export = True


# ─── Widget & Guests ─────────────────────────────────────────────────────────

class WidgetSettingsAdmin(ModelView, model=WidgetSettings):
    name = "Widget"
    name_plural = "Widgets"
    icon = "fa-solid fa-puzzle-piece"
    category = "Widget & Guests"

    column_list = [
        WidgetSettings.id, WidgetSettings.user_id, WidgetSettings.public_widget_id,
        WidgetSettings.theme, WidgetSettings.is_active, WidgetSettings.whatsapp_enabled,
        WidgetSettings.created_at,
    ]
    column_details_exclude_list = [WidgetSettings.whatsapp_access_token]
    column_searchable_list = [WidgetSettings.user_id, WidgetSettings.public_widget_id]
    column_sortable_list = [WidgetSettings.is_active, WidgetSettings.created_at, WidgetSettings.theme]
    column_default_sort = ("created_at", True)

    form_excluded_columns = [
        WidgetSettings.whatsapp_access_token,
        WidgetSettings.created_at, WidgetSettings.updated_at,
    ]

    column_labels = {
        "user_id": "Owner",
        "public_widget_id": "Public ID",
        "is_active": "Active",
        "whatsapp_enabled": "WhatsApp",
        "max_messages_per_session": "Max Msgs/Session",
        "max_sessions_per_day": "Max Sessions/Day",
    }

    can_export = True


class GuestUserAdmin(ModelView, model=GuestUser):
    name = "Guest"
    name_plural = "Guests"
    icon = "fa-solid fa-user-secret"
    category = "Widget & Guests"

    column_list = [
        GuestUser.id, GuestUser.widget_id, GuestUser.name, GuestUser.email,
        GuestUser.is_lead, GuestUser.is_returning, GuestUser.total_sessions,
        GuestUser.created_at,
    ]
    column_searchable_list = [GuestUser.name, GuestUser.email, GuestUser.phone, GuestUser.widget_id]
    column_sortable_list = [
        GuestUser.name, GuestUser.created_at, GuestUser.total_sessions,
        GuestUser.is_lead, GuestUser.is_returning,
    ]
    column_default_sort = ("created_at", True)

    can_create = False
    form_excluded_columns = [GuestUser.created_at, GuestUser.first_seen_at]

    column_labels = {
        "widget_id": "Widget",
        "is_lead": "Lead",
        "is_returning": "Returning",
        "total_sessions": "Sessions",
    }

    can_export = True


# ─── Documents ───────────────────────────────────────────────────────────────

class DocumentAdmin(ModelView, model=Document):
    name = "Document"
    name_plural = "Documents"
    icon = "fa-solid fa-file"
    category = "Documents"

    column_list = [Document.id, Document.user_id, Document.filename, Document.status, Document.created_at]
    column_searchable_list = [Document.user_id, Document.filename, Document.status]
    column_sortable_list = [Document.filename, Document.status, Document.created_at]
    column_default_sort = ("created_at", True)

    form_excluded_columns = [Document.created_at]

    column_labels = {"user_id": "Owner", "file_path": "Path", "error_message": "Error"}

    can_export = True


# ─── Analytics ───────────────────────────────────────────────────────────────

class AnalyticsDailySummaryAdmin(ModelView, model=AnalyticsDailySummary):
    name = "Daily Summary"
    name_plural = "Daily Summaries"
    icon = "fa-solid fa-chart-bar"
    category = "Analytics"

    column_list = [
        AnalyticsDailySummary.id, AnalyticsDailySummary.business_id,
        AnalyticsDailySummary.date, AnalyticsDailySummary.total_sessions,
        AnalyticsDailySummary.total_guests, AnalyticsDailySummary.leads_captured,
        AnalyticsDailySummary.top_intent,
    ]
    column_searchable_list = [AnalyticsDailySummary.business_id, AnalyticsDailySummary.top_intent]
    column_sortable_list = [
        AnalyticsDailySummary.date, AnalyticsDailySummary.total_sessions,
        AnalyticsDailySummary.total_guests, AnalyticsDailySummary.leads_captured,
    ]
    column_default_sort = ("date", True)

    can_create = False
    can_delete = False
    form_excluded_columns = [AnalyticsDailySummary.created_at, AnalyticsDailySummary.updated_at]

    column_labels = {
        "business_id": "Business",
        "total_sessions": "Sessions",
        "total_guests": "Guests",
        "new_guests": "New",
        "returning_guests": "Returning",
        "leads_captured": "Leads",
    }

    can_export = True
