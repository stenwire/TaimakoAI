import os
import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.widget import GuestMessage, GuestUser
from app.models.chat_session import ChatSession

# Using hypothetical google.generativeai for the agent as per project patterns
import google.generativeai as genai

# For simplicity, assuming environment key is set
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

INTENT_ENUM = ["Support", "Sales", "Feedback", "Bug Report", "General"]

async def analyze_session(db: Session, session_id: str, intents: Optional[List[str]] = None) -> Tuple[str, str]:
    """
    Analyzes a chat session to generate a summary and determine intent.
    Returns (summary, intent).
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")
        
    messages = db.query(GuestMessage).filter(GuestMessage.session_id == session_id).order_by(GuestMessage.created_at).all()
    
    if not messages:
        return "No messages in session", "General"
        
    conversation_text = ""
    for msg in messages:
        role = "User" if msg.sender == "guest" else "Agent"
        conversation_text += f"{role}: {msg.message_text}\n"
        
    # Use provided intents or fallback to default
    intent_list = intents if intents and len(intents) > 0 else INTENT_ENUM
        
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
        model = genai.GenerativeModel("gemini-2.0-flash") # Or pro
        response = model.generate_content(prompt)
        
        # Simple parsing logic (assuming well-behaved model or using response_schema in future)
        content = response.text
        # Strip code blocks if present
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        elif "```" in content:
            content = content.replace("```", "")
            
        data = json.loads(content)
        
        summary = data.get("summary", "Unable to generate summary")
        intent = data.get("intent", "Unable to get Intent")
        
        # specific validation
        if intent not in intent_list:
            if "General" in intent_list:
                intent = "General"
            else:
                intent = intent_list[-1] # Fallback to last item or just keep raw if model hallucinates slightly? Safe to map to first/last.
            
        return summary, intent
        
    except Exception as e:
        print(f"Error in analysis agent: {e}")
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
    if session:
        session.summary = summary
        session.top_intent = intent
        session.summary_generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        return session
    return None

async def generate_business_intents(business_description: str) -> List[str]:
    prompt = f"""
    You are a Business Consultant. Based on the following business description, generate exactly 5 intent categories that customers of this business might have.
    
    Business Description:
    {business_description}
    
    Output a JSON array of 5 strings. Example: ["Order Status", "Return Policy", "Product Info", "Technical Support", "Hours of Operation"]
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
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

async def generate_followup_content(messages: List[GuestMessage], follow_up_type: str, extra_info: str) -> str:
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
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating follow up: {e}")
        return "Error generating follow up."
