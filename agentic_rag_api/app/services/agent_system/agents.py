from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm 
from app.services.agent_system.tools import get_context, say_hello, say_goodbye
from app.services.agent_system.callbacks import block_unsafe_content, validate_tool_args

# --- Model Constants ---
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# Sub-Agent: Greeting
greeting_agent = Agent(
    name="greeting_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Handles simple greetings.",
    instruction="You are a friendly greeting agent. Use 'say_hello' to greet the user.",
    tools=[say_hello]
)

# Sub-Agent: Farewell
farewell_agent = Agent(
    name="farewell_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Handles simple farewells.",
    instruction="You are a polite farewell agent. Use 'say_goodbye' to say goodbye.",
    tools=[say_goodbye]
)

# Root Agent: RAG (Multi-Model, Delegation, State, Guardrails)
rag_agent = Agent(
    name="rag_agent",
    # Using LiteLlm wrapper for multi-model support (even if using Gemini here)
    model=MODEL_GEMINI_2_0_FLASH, 
    description="Main agent. Provides context for questions, delegates greetings/farewells.",
    instruction="You are a helpful customer support assistant. "
                "For greetings, delegate to 'greeting_agent'. "
                "For farewells, delegate to 'farewell_agent'. "
                "For questions, use 'get_context' to find relevant info. "
                "Present the context clearly.",
    tools=[get_context],
    sub_agents=[greeting_agent, farewell_agent],
    output_key="last_agent_response", # Save final response to session state
    before_model_callback=block_unsafe_content,
    before_tool_callback=validate_tool_args
)
