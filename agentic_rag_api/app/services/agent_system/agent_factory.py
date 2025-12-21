from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm 
from app.services.agent_system.tools import get_context, say_hello, say_goodbye
from app.services.agent_system.callbacks import block_unsafe_content, validate_tool_args
from typing import Optional

# Default detailed instruction used when a business does not provide a custom one.
# This follows best practices: be friendly, professional, concise, and reference the business name.
DEFAULT_AGENT_INSTRUCTION = (
    "You are a helpful, friendly, and professional customer support assistant. "
    "Always address the user politely, reference the business name where appropriate, and "
    "provide concise, accurate answers based on the provided context. "
    "If you do not know the answer, admit it and suggest how the user might obtain the information. "
    "Maintain a tone that reflects the brand's values and ensure data privacy."
)


# --- Model Constants ---
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

class AgentFactory:
    """Factory for creating dynamically configured agents based on business settings."""
    
    @staticmethod
    def create_greeting_agent():
        """Create the greeting sub-agent."""
        return Agent(
            name="greeting_agent",
            model=MODEL_GEMINI_2_0_FLASH,
            description="Handles simple greetings.",
            instruction="You are a friendly greeting agent. Use 'say_hello' to greet the user.",
            tools=[say_hello]
        )
    
    @staticmethod
    def create_farewell_agent():
        """Create the farewell sub-agent."""
        return Agent(
            name="farewell_agent",
            model=MODEL_GEMINI_2_0_FLASH,
            description="Handles simple farewells.",
            instruction="You are a polite farewell agent. Use 'say_goodbye' to say goodbye.",
            tools=[say_goodbye]
        )
    
    @staticmethod
    def create_rag_agent(business_name: str, custom_instruction: Optional[str] = None, intents: Optional[list] = None):
        """
        Create a RAG agent with business-specific configuration.
        
        Args:
            business_name: Name of the business
            custom_instruction: Optional custom instructions for the agent
            intents: Optional list of business intents
            
        Returns:
            Configured Agent instance
        """
        # Build the instruction with business context
        base_instruction = f"You are a helpful customer support assistant for {business_name}. "
        
        # Use provided custom instruction or fallback to the default detailed placeholder
        instruction_to_use = custom_instruction if custom_instruction else DEFAULT_AGENT_INSTRUCTION
        base_instruction += f"{instruction_to_use}\n\n"
        
        if intents:
            base_instruction += f"The business has defined the following key intents: {', '.join(intents)}. Keep these in mind when determining the user's intent.\n\n"
        
        base_instruction += (
            "For greetings, delegate to 'greeting_agent'. "
            "For farewells, delegate to 'farewell_agent'. "
            "For questions, use 'get_context' to find relevant info. "
            "Present the context clearly."
        )
        
        # Create sub-agents
        greeting_agent = AgentFactory.create_greeting_agent()
        farewell_agent = AgentFactory.create_farewell_agent()
        
        # Create and return the main RAG agent
        return Agent(
            name="rag_agent",
            model=MODEL_GEMINI_2_0_FLASH, 
            description=f"Main agent for {business_name}. Provides context for questions, delegates greetings/farewells.",
            instruction=base_instruction,
            tools=[get_context],
            sub_agents=[greeting_agent, farewell_agent],
            output_key="last_agent_response",
            before_model_callback=block_unsafe_content,
            before_tool_callback=validate_tool_args
        )
