"""
Factory classes for test data generation using factory-boy.
Provides consistent, reusable test data for all model types.
"""
import factory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime, timezone
import uuid

from app.models.user import User
from app.models.business import Business
from app.models.widget import WidgetSettings, GuestUser, GuestMessage
from app.models.chat_session import ChatSession, SessionOrigin
from app.models.escalation import Escalation, EscalationStatus


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""
    
    class Meta:
        abstract = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to use the session from Meta."""
        session = cls._meta.sqlalchemy_session
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.flush()
        return obj


class UserFactory(BaseFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    name = factory.Faker("name")
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    google_id = None
    picture = None
    hashed_password = None


class BusinessFactory(BaseFactory):
    """Factory for creating Business instances."""
    
    class Meta:
        model = Business
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.SelfAttribute("user.id")
    user = factory.SubFactory(UserFactory)
    business_name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=200)
    website = factory.Faker("url")
    custom_agent_instruction = "Be helpful and friendly."
    intents = None
    is_escalation_enabled = False
    escalation_emails = None
    logo_url = None
    gemini_api_key = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    
    class Params:
        escalation_ready = factory.Trait(
            is_escalation_enabled=True,
            escalation_emails=["escalation@test.com", "support@test.com"]
        )


class WidgetSettingsFactory(BaseFactory):
    """Factory for creating WidgetSettings instances."""
    
    class Meta:
        model = WidgetSettings
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.SelfAttribute("user.id")
    user = factory.SubFactory(UserFactory)
    public_widget_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    theme = "light"
    primary_color = "#000000"
    icon_url = None
    welcome_message = "Hi there! 👋"
    initial_ai_message = "How can I help you today?"
    send_initial_message_automatically = True
    whatsapp_enabled = False
    whatsapp_number = None
    is_active = True
    logo_url = None
    max_messages_per_session = 50
    max_sessions_per_day = 5
    whitelisted_domains = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class GuestUserFactory(BaseFactory):
    """Factory for creating GuestUser instances."""
    
    class Meta:
        model = GuestUser
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    widget_id = factory.SelfAttribute("widget.id")
    widget = factory.SubFactory(WidgetSettingsFactory)
    name = factory.Faker("name")
    email = factory.Faker("email")
    phone = factory.Faker("phone_number")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    first_seen_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    last_seen_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    total_sessions = 0
    is_returning = False
    is_lead = False


class ChatSessionFactory(BaseFactory):
    """Factory for creating ChatSession instances."""
    
    class Meta:
        model = ChatSession
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    guest_id = factory.SelfAttribute("guest.id")
    guest = factory.SubFactory(GuestUserFactory)
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    last_message_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    origin = SessionOrigin.AUTO_START.value
    summary = None
    summary_generated_at = None
    top_intent = None
    sentiment_score = None
    is_active = True
    device_type = "desktop"
    browser = "Chrome"
    os = "macOS"
    country = None
    city = None
    timezone = None
    referrer = None
    utm_source = None
    utm_medium = None
    utm_campaign = None
    session_duration = 0
    total_messages = 0
    user_messages = 0
    ai_messages = 0
    first_response_time = None


class EscalationFactory(BaseFactory):
    """Factory for creating Escalation instances."""
    
    class Meta:
        model = Escalation
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    business_id = factory.SelfAttribute("business.id")
    business = factory.SubFactory(BusinessFactory)
    session_id = factory.SelfAttribute("session.id")
    session = factory.SubFactory(ChatSessionFactory)
    status = EscalationStatus.PENDING.value
    summary = factory.Faker("text", max_nb_chars=200)
    sentiment = "Negative"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class GuestMessageFactory(BaseFactory):
    """Factory for creating GuestMessage instances."""
    
    class Meta:
        model = GuestMessage
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    guest_id = factory.SelfAttribute("guest.id")
    guest = factory.SubFactory(GuestUserFactory)
    session_id = factory.SelfAttribute("session.id")
    session = factory.SubFactory(ChatSessionFactory)
    sender = "guest"
    message_text = factory.Faker("sentence")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
