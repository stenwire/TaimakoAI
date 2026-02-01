import os
import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.widget import GuestMessage, GuestUser
from app.models.chat_session import ChatSession

# Use specific client for multi-tenant API key support
from google import genai

INTENT_ENUM = ["Support", "Sales", "Feedback", "Bug Report", "General"]

async def analyze_session(db: Session, session_id: str, intents: Optional[List[str]] = None, api_key: str = None) -> Tuple[str, str]:
    """
    Analyzes a chat session to generate a summary and determine intent.
    Returns (summary, intent).
    """
    print(f"\n=== Analysis Agent: Starting analysis for session {session_id} ===")
    
    if not api_key:
        # Fail fast if no key provided
        print("Analysis Agent: No API Key provided")
        return "Analysis unavailable (Missing Key)", "General"

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        print(f"Analysis Agent: Session {session_id} not found in database")
        raise ValueError("Session not found")
        
    messages = db.query(GuestMessage).filter(GuestMessage.session_id == session_id).order_by(GuestMessage.created_at).all()
    
    print(f"Analysis Agent: Found {len(messages)} messages in session")
    
    if not messages:
        print("Analysis Agent: No messages to analyze")
        return "No messages in session", "General"
        
    conversation_text = ""
    for msg in messages:
        role = "User" if msg.sender == "guest" else "Agent"
        conversation_text += f"{role}: {msg.message_text}\n"
    
    # Show conversation preview for debugging
    preview = conversation_text[:200] + "..." if len(conversation_text) > 200 else conversation_text
    print(f"Analysis Agent: Conversation preview:\n{preview}")
        
    # Use provided intents or fallback to default
    intent_list = intents if intents and len(intents) > 0 else INTENT_ENUM
    print(f"Analysis Agent: Using intent categories: {intent_list}")
        
    # Construct Prompt
    prompt = f"""
    You are an expert Conversation Analyst. Your task is to analyze the following chat transcript between a User and an AI Agent.
    
    Existing Summary: {session.summary or "None"}
    Existing Intent: {session.top_intent or "None"}
    
    TRANSCRIPT:
    {conversation_text}
    
    INSTRUCTIONS:
    1. Generate a concise summary of the conversation (max 2-3 sentences). usage: "User asked about X, Agent provided Y."
    2. Determine the Top Intent from this list: {intent_list}.
    3. If an existing summary exists, use it as context but update it to reflect the full conversation.
    
    Output correctly formatted JSON only:
    {{
        "summary": "...",
        "intent": "..."
    }}
    """
    
    try:
        print(f"Analysis Agent: Calling Gemini 2.0 Flash for analysis...")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        
        # Simple parsing logic
        content = response.text
        print(f"Analysis Agent: Raw LLM response: {content[:150]}...")
        
        # Strip code blocks if present
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
            content = content.replace("```", "")
            
        data = json.loads(content)
        
        summary = data.get("summary", "Unable to generate summary")
        intent = data.get("intent", "Unable to get Intent")
        
        print(f"Analysis Agent: Parsed summary: '{summary}'")
        print(f"Analysis Agent: Parsed intent: '{intent}'")
        
        # specific validation
        if intent not in intent_list:
            print(f"Analysis Agent: Intent '{intent}' not in allowed list, defaulting to 'General'")
            if "General" in intent_list:
                intent = "General"
            else:
                intent = intent_list[-1] 
        
        print(f"=== Analysis Agent: Complete - Summary length: {len(summary)} chars, Intent: {intent} ===\n")
        return summary, intent
        
    except Exception as e:
        print(f"Analysis Agent: Error during analysis: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return session.summary or "Error generating summary", session.top_intent or "General"

async def persist_analysis(db: Session, session_id: str, summary: str, intent: str):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.summary = summary
        session.top_intent = intent
        session.summary_generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        return session
    return None

async def generate_business_intents(business_description: str, api_key: str = None) -> List[str]:
    if not api_key:
        return []

    prompt = f"""
    You are a Business Consultant. Based on the following business description, generate exactly 5 intent categories that customers of this business might have.
    
    Business Description:
    {business_description}
    
    Output a JSON array of 5 strings. Example: ["Order Status", "Return Policy", "Product Info", "Technical Support", "Hours of Operation"]
    """
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = response.text
        if "```json" in text:
            text = text.replace("```json", "").replace("```", "")
        elif "```" in text:
            text = text.replace("```", "")
            
        intents = json.loads(text)
        if isinstance(intents, list):
            return intents[:5]
        return []
    except Exception as e:
        print(f"Error generating intents: {e}")
        return []

async def generate_followup_content(messages: List[GuestMessage], follow_up_type: str, extra_info: str, api_key: str = None) -> str:
    if not api_key:
        return "Error: No API Key configured."

    conversation_text = ""
    for msg in messages:
        role = "User" if msg.sender == "guest" else "Agent"
        conversation_text += f"{role}: {msg.message_text}\n"
    
    prompt = f"""
    You are an AI assistant helping a business follow up with a customer based on a chat session.
    
    TRANSCRIPT:
    {conversation_text}
    
    TASK: Generate a {follow_up_type} for the customer.
    
    ADDITIONAL CONTEXT FROM BUSINESS:
    {extra_info}
    
    INSTRUCTIONS:
    - If email, include Subject and Body.
    - If transcript, clean it up and summarize key points first.
    - Be professional and polite.
    """
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error generating follow up: {e}")
        return "Error generating follow up."

