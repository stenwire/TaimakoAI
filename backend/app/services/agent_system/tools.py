from typing import Optional
from google.adk.tools.tool_context import ToolContext
from app.services.agent_system.tool_schemas import (
    GetContextInput, ContextOutput,
    SayHelloInput, GreetingOutput,
    SayGoodbyeInput, FarewellOutput
)
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.escalation import Escalation, EscalationStatus
from app.models.chat_session import ChatSession
from app.services.email_service import EmailServiceFactory
from app.services.agent_system.tool_schemas import (
    AnalyzeSentimentInput, AnalyzeSentimentOutput,
    EscalateToHumanInput, EscalateToHumanOutput
)
import json

try:
    from google import genai
except ImportError:
    genai = None

# Mock RAG Service import (handling missing dependencies as done previously)
try:
    from app.services.rag_service import rag_service
except ImportError:
    print("Warning: RAG Service dependencies missing. Using Mock RAG Service.")
    class MockRAGService:
        def query(self, text, user_id=None, api_key=None):
            return [f"Mock context for: {text}"]
    rag_service = MockRAGService()

def get_context(user_input: str, tool_context: ToolContext) -> str:
    """Retrieves context from the RAG service using structured schemas.

    Args:
        user_input: The user's input message.
        tool_context: The tool context to access session state.

    Returns:
        str: The retrieved context as a formatted string.
    """
    print(f"--- Tool: get_context called for user_input: {user_input} ---")
    
    # Validate input using Pydantic schema
    try:
        validated_input = GetContextInput(user_input=user_input)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"
    
    # Extract user_id from state
    user_id = tool_context.state.get("user_id")
    if not user_id:
        return "Error: User ID not found in session state."
    
    # Extract api_key from state
    api_key = tool_context.state.get("api_key")
    if not api_key:
        print(f"Warning: Tool get_context missing api_key for user {user_id}")
        return "Error: API Key configuration missing. Cannot access knowledge base."

    # Example of reading from state
    style = tool_context.state.get("response_style", "normal")
    print(f"--- Tool: Reading state 'response_style': {style} ---")
    print(f"--- Tool: Using user_id: {user_id} ---")

    # Retrieve context with user_id and api_key
    context_chunks = rag_service.query(text=validated_input.user_input, user_id=user_id, api_key=api_key)
    print(f"--- Tool: RAG Service returned {len(context_chunks)} chunks ---")
    
    # Create structured output
    output = ContextOutput(
        context_text="\n\n".join(context_chunks),
        chunks_count=len(context_chunks)
    )
    
    # Return as string for ADK compatibility
    return output.context_text

def say_hello(name: Optional[str] = None) -> str:
    """Provides a greeting using structured schemas.

    Args:
        name: Optional name of the person to greet.

    Returns:
        str: A friendly greeting message.
    """
    # Validate input using Pydantic schema
    try:
        validated_input = SayHelloInput(name=name)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"
    
    if validated_input.name:
        message = f"Hello, {validated_input.name}! How can I help you today?"
    else:
        message = "Hello! How can I assist you with your questions?"
    
    # Create structured output
    output = GreetingOutput(message=message)
    return output.message

def say_goodbye() -> str:
    """Provides a farewell message using structured schemas.
    
    Returns:
        str: A polite farewell message.
    """
    # Validate input (empty schema for this tool)
    validated_input = SayGoodbyeInput()
    
    # Create structured output
    output = FarewellOutput(message="Goodbye! Have a great day.")
    return output.message

def analyze_sentiment(user_text: str, tool_context: ToolContext) -> str:
    """Analyzes the sentiment of the user's text.
    
    Args:
        user_text: The input text to analyze.
        tool_context: Context containing API key.
        
    Returns:
        JSON string with sentiment and score.
    """
    print(f"--- Tool: analyze_sentiment called for: {user_text} ---")
    
    # 1. Validate Input
    try:
        validated_input = AnalyzeSentimentInput(user_text=user_text)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"

    api_key = tool_context.state.get("api_key")
    
    sentiment = "Neutral"
    score = 0.5
    
    # 2. Use Gemini if available
    if api_key and genai:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Analyze the sentiment of the following text.
            Text: "{validated_input.user_text}"
            
            Return JSON only: {{"sentiment": "Positive" | "Neutral" | "Negative", "score": 0.0 to 1.0}}
            """
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            sentiment = data.get("sentiment", "Neutral")
            score = data.get("score", 0.5)
        except Exception as e:
            print(f"Sentiment Analysis Error: {e}")
            # Fallback based on keywords
            lower_text = validated_input.user_text.lower()
            if any(w in lower_text for w in ["angry", "bad", "terrible", "hate", "scam"]):
                sentiment = "Negative"
                score = 0.9
            elif any(w in lower_text for w in ["good", "great", "love", "thanks"]):
                sentiment = "Positive"
                score = 0.9

    # 3. Return Output
    output = AnalyzeSentimentOutput(sentiment=sentiment, score=score)
    # Storing sentiment in state for other tools to use if needed
    tool_context.state["last_sentiment"] = sentiment
    
    return json.dumps(output.model_dump())

def escalate_to_human(reason: str, user_message: str, tool_context: ToolContext) -> str:
    """Escalates the conversation to a human agent.
    
    Args:
        reason: Why the escalation is happening.
        user_message: The user's message triggering it.
        
    Returns:
        Confirmation message.
    """
    print(f"--- Tool: escalate_to_human called. Reason: {reason} ---")
    
    # 1. Validate Input
    try:
        validated_input = EscalateToHumanInput(reason=reason, user_message=user_message)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"

    session_id = tool_context.state.get("session_id")
    
    if not session_id:
        session_id = tool_context.state.get("session_id")
        
    if not session_id:
        return "Error: Session ID missing from context. Cannot escalate."

    db = SessionLocal()
    try:
        # 2. Get Session and Business
        # 2. Get Session and Business using sequential queries (avoiding join ambiguity)
        print(f"Escalation: Fetching session {session_id}")
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        
        if not chat_session:
            print(f"Escalation Error: Session {session_id} not found")
            return "Error: Chat Session not found."
        
        print(f"Escalation: Session found. Guest ID: {chat_session.guest_id}")
        
        # Get guest user
        if not chat_session.guest:
            print(f"Escalation Error: No guest associated with session {session_id}")
            return "Error: Guest user not found."
        
        guest = chat_session.guest
        print(f"Escalation: Guest found. Widget ID: {guest.widget_id}")
        
        # Get widget settings
        if not guest.widget:
            print(f"Escalation Error: No widget associated with guest {guest.id}")
            return "Error: Widget not found."
        
        widget = guest.widget
        print(f"Escalation: Widget found. User ID: {widget.user_id}")
        
        # Get business via user_id
        from app.models.user import User
        business = db.query(Business).filter(Business.user_id == widget.user_id).first()
        
        if not business:
            print(f"Escalation Error: No business found for user {widget.user_id}")
            return "Error: Business not found."
        
        print(f"Escalation: Business found. Name: {business.business_name}, Escalation enabled: {business.is_escalation_enabled}")

        # 3. Check if enabled
        if not business.is_escalation_enabled:
            return "I apologize, but human escalation is currently not available for this service."

        # 4. Create Escalation
        escalation = Escalation(
            business_id=business.id,
            session_id=session_id,
            summary=f"Escalation Triggered: {validated_input.reason}\nUser Message: {validated_input.user_message}",
            sentiment="Negative", # Default or should be passed.
            status=EscalationStatus.PENDING.value
        )
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        
        # 5. Send Email
        email_service = EmailServiceFactory.get_service()
        emails = business.escalation_emails or []
        if emails:
            subject = f"Escalation Alert: {business.business_name}"
            body = (
                f"New Escalation Request.\n"
                f"Session ID: {session_id}\n"
                f"Reason: {validated_input.reason}\n"
                f"User Message: {validated_input.user_message}\n"
            )
            email_service.send_email(emails, subject, body)
            
        output = EscalateToHumanOutput(
            escalation_id=escalation.id,
            status="pending",
            message="Your request has been forwarded to a human agent. Only a summary will be shared."
        )
        
        return json.dumps(output.model_dump())
        
    except Exception as e:
        print(f"Escalation Error: {e}")
        return f"Error processing escalation: {str(e)}"
    finally:
        db.close()
