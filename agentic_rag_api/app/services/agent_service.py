try:
    from app.services.rag_service import rag_service
except ImportError:
    print("Warning: RAG Service dependencies missing. Using Mock RAG Service.")
    class MockRAGService:
        def query(self, text, user_id):
            return [f"Mock context for: {text}"]
    rag_service = MockRAGService()

# Backward compatible constants for tests and legacy code
APP_NAME = "agentic_rag_api"
USER_ID = "test_user"
SESSION_ID = "test_session"

import os
import asyncio
from google.adk.runners import Runner
from google.genai import types 
import logging
from typing import Optional

# Import from new modular structure
from app.services.agent_system.service import session_service, init_session
from app.services.agent_system.agent_factory import AgentFactory

import warnings
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.ERROR)

print("Libraries imported.")
print(f"Google API Key set: {'Yes' if os.environ.get('GOOGLE_API_KEY') and os.environ['GOOGLE_API_KEY'] != 'YOUR_GOOGLE_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")


async def call_agent_async(query: str, runner: Runner, user_id: str, session_id: str):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query} (User: {user_id})")

    content = types.Content(role='user', parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response." 

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # print(f"  [Event] {type(event).__name__}") # Uncomment for debug
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break 

    print(f"<<< Agent Response: {final_response_text}")
    return final_response_text


async def run_conversation(
    message: str,
    user_id: str = USER_ID,
    business_name: str = APP_NAME,
    custom_instruction: Optional[str] = None,
    session_id: Optional[str] = None,
    intents: Optional[list] = None
):
    """
    Run a conversation with a dynamically configured agent.
    
    Args:
        message: User's message
        user_id: User identifier
        business_name: Name of the business
        custom_instruction: Optional custom agent instructions
        session_id: Optional session identifier (defaults to user_id)
        intents: Optional list of business intents
        
    Returns:
        Agent's response text
    """
    if session_id is None:
        session_id = user_id
    
    # Create agent dynamically based on business configuration
    agent = AgentFactory.create_rag_agent(business_name, custom_instruction, intents=intents)
    
    # Create runner with dynamic agent
    runner = Runner(
        agent=agent,
        app_name=business_name,
        session_service=session_service
    )
    
    # Initialize session with user_id in state
    initial_state = {
        "response_style": "concise",
        "user_id": user_id  # Store user_id for tools to access
    }
    await init_session(business_name, user_id, session_id, initial_state)
    
    return await call_agent_async(
        message,
        runner=runner,
        user_id=user_id,
        session_id=session_id
    )

