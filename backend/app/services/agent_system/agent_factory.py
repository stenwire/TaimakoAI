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
    def _get_model(api_key: Optional[str] = None):
        """Get the appropriate model, with API key if provided."""
        if api_key:
            model_name = MODEL_GEMINI_2_0_FLASH
            if not model_name.startswith("gemini/"):
                model_name = f"gemini/{model_name}"
            return LiteLlm(model=model_name, api_key=api_key)
        return MODEL_GEMINI_2_0_FLASH
    
    @staticmethod
    def create_greeting_agent(api_key: Optional[str] = None):
        """Create the greeting sub-agent."""
        return Agent(
            name="greeting_agent",
            model=AgentFactory._get_model(api_key),
            description="Handles simple greetings.",
            instruction="You are a friendly greeting agent. Use 'say_hello' to greet the user.",
            tools=[say_hello]
        )
    
    @staticmethod
    def create_farewell_agent(api_key: Optional[str] = None):
        """Create the farewell sub-agent."""
        return Agent(
            name="farewell_agent",
            model=AgentFactory._get_model(api_key),
            description="Handles simple farewells.",
            instruction="You are a polite farewell agent. Use 'say_goodbye' to say goodbye.",
            tools=[say_goodbye]
        )
    
    @staticmethod
    def create_rag_agent(business_name: str, custom_instruction: Optional[str] = None, intents: Optional[list] = None, api_key: Optional[str] = None):
        """
        Create a RAG agent with business-specific configuration.
        This agent is a specialist in retrieving context and answering questions.
        
        Args:
            business_name: Name of the business
            custom_instruction: Optional custom instructions for the agent
            intents: Optional list of business intents
            api_key: API Key for the model
            
        Returns:
            Configured Agent instance
        """
        # Determine model to use - API key is required
        if not api_key:
            raise ValueError("API Key is required for this business configuration.")
        
        # Build the instruction with business context
        base_instruction = f"You are a helpful customer support assistant for {business_name}. "
        
        # Use provided custom instruction or fallback to the default detailed placeholder
        instruction_to_use = custom_instruction if custom_instruction else DEFAULT_AGENT_INSTRUCTION
        base_instruction += f"{instruction_to_use}\n\n"
        
        if intents:
            base_instruction += f"The business has defined the following key intents: {', '.join(intents)}. Keep these in mind when determining the user's intent.\n\n"
        
        base_instruction += (
            "Your role is to answer questions using the 'get_context' tool. "
            "Do not handle greetings or farewells directly if they are just pleasantries; "
            "however, if a question is mixed with a greeting, answer the question."
        )

        model = AgentFactory._get_model(api_key)

        # Create and return the RAG agent
        return Agent(
            name="rag_agent",
            model=model, 
            description=f"Specialist agent for {business_name}. Provides context and answers business questions.",
            instruction=base_instruction,
            tools=[get_context],
            sub_agents=[],
            output_key="last_agent_response",
            before_model_callback=block_unsafe_content,
            before_tool_callback=validate_tool_args
        )

    @staticmethod
    def create_chief_agent(business_name: str, custom_instruction: Optional[str] = None, intents: Optional[list] = None, api_key: Optional[str] = None):
        """
        Create the Chief Agent (Orchestrator) that manages other agents.
        """
        if not api_key:
            raise ValueError("API Key is required for this business configuration.")
            
        # Create sub-agents
        greeting_agent = AgentFactory.create_greeting_agent(api_key)
        farewell_agent = AgentFactory.create_farewell_agent(api_key)
        rag_agent = AgentFactory.create_rag_agent(business_name, custom_instruction, intents, api_key)
        
        instruction = (
            f"You are the Chief Agent for {business_name}. Your role is to coordinate the conversation warmly and efficiently.\n"
            "Delegate to 'greeting_agent' for simple greetings.\n"
            "Delegate to 'farewell_agent' for farewells.\n"
            "Delegate to 'rag_agent' for any business-specific questions, information requests, or if the user needs help with the service.\n"
            "If the user input is ambiguous, try to help but prioritize delegating to the 'rag_agent' if it seems like a question."
        )

        return Agent(
            name="chief_agent",
            model=AgentFactory._get_model(api_key),
            description=f"Chief Orchestrator Agent for {business_name}.",
            instruction=instruction,
            # No tools for the chief directly, it delegates. 
            # (Unless we want it to have some general tools, but purely orchestrator for now is safer)
            tools=[], 
            sub_agents=[greeting_agent, farewell_agent, rag_agent],
            output_key="last_agent_response",
            before_model_callback=block_unsafe_content
        )
