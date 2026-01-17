from typing import Optional
from google.adk.tools.tool_context import ToolContext
from app.services.agent_system.tool_schemas import (
    GetContextInput, ContextOutput,
    SayHelloInput, GreetingOutput,
    SayGoodbyeInput, FarewellOutput
)

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
