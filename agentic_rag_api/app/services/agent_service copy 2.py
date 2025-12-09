from distro.distro import name
import google.generativeai as genai
from app.core.config import settings
from app.services.rag_service import rag_service
from app.models.chat import ChatResponse

import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts


import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

print("Libraries imported.")
print(f"Google API Key set: {'Yes' if os.environ.get('GOOGLE_API_KEY') and os.environ['GOOGLE_API_KEY'] != 'YOUR_GOOGLE_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# --- Session Management ---
# Key Concept: SessionService stores conversation history & state.
# InMemorySessionService is simple, non-persistent storage for this tutorial.
session_service = InMemorySessionService()

# Define constants for identifying the interaction context
APP_NAME = "customer_support_app"
USER_ID = "user_1"
SESSION_ID = "session_001" # Using a fixed ID for now

async def init_session(app_name:str, user_id:str, session_id:str) -> InMemorySessionService:
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    print(f"Session created: App='{app_name}', User='{user_id}', Session='{session_id}'")
    return session

# session = asyncio.run(init_session(APP_NAME,USER_ID,SESSION_ID))


def get_context(user_input: str) -> str:
    """Retrieves the context from the RAG service.

    Args:
        user_input (str): The user's input message.

    Returns:
        str: The retrieved context.
    """
    print(f"--- Tool: get_context called for user_input: {user_input} ---") # Log tool execution
    # Retrieve context
    context_chunks = rag_service.query(user_input)
    context_text = "\n\n".join(context_chunks)
    return context_text

rag_agent = Agent(
    name="rag_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Provides context to the user based on the user's input.",
    instruction="You are a helpful customer support assistant. "
                "When the user asks a question, "
                "use the 'get_context' tool to find context relevant to the user's question. "
                "If the tool returns an error, inform the user politely. "
                "If the tool is successful, present the context clearly and how it relates to the user's question.",
    tools=[
        get_context
    ]
)

# --- Runner ---
# Key Concept: Runner orchestrates the agent execution loop.
runner = Runner(
    agent=rag_agent, # The agent we want to run
    app_name=APP_NAME,   # Associates runs with our app
    session_service=session_service # Uses our session manager
)
print(f"Runner created for agent '{runner.agent.name}'.")

async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response." # Default

    # Key Concept: run_async executes the agent logic and yields Events.
    # We iterate through events to find the final answer.
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # You can uncomment the line below to see *all* events during execution
        print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            # Add more checks here if needed (e.g., specific error codes)
            break # Stop processing events once the final response is found

    print(f"<<< Agent Response: {final_response_text}")
    return final_response_text


async def run_conversation(message):
    return await call_agent_async(
        message,
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

# import asyncio
# if __name__ == "__main__":
#     try:
#         asyncio.run(run_conversation("What are stephen skills?"))
#     except Exception as e:
#         print(f"An error occurred: {e}")

