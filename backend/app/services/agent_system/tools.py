from typing import Optional
from google.adk.tools.tool_context import ToolContext

# Mock RAG Service import (handling missing dependencies as done previously)
try:
    from app.services.rag_service import rag_service
except ImportError:
    print("Warning: RAG Service dependencies missing. Using Mock RAG Service.")
    class MockRAGService:
        def query(self, text):
            return [f"Mock context for: {text}"]
    rag_service = MockRAGService()

def get_context(user_input: str, tool_context: ToolContext) -> str:
    """Retrieves the context from the RAG service.

    Args:
        user_input (str): The user's input message.
        tool_context (ToolContext): The tool context to access session state.

    Returns:
        str: The retrieved context.
    """
    print(f"--- Tool: get_context called for user_input: {user_input} ---") 
    
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
    context_chunks = rag_service.query(text=user_input, user_id=user_id, api_key=api_key)
    print(f"--- Tool: RAG Service returned {len(context_chunks)} chunks ---")
    context_text = "\n\n".join(context_chunks)
    return context_text

def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting.

    Args:
        name (str, optional): The name of the person to greet.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        return f"Hello, {name}! How can I help you today?"
    return "Hello! How can I assist you with your questions?"

def say_goodbye() -> str:
    """Provides a simple farewell message."""
    return "Goodbye! Have a great day."
