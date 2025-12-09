from typing import Optional, Dict, Any
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types 

def block_unsafe_content(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Blocks requests containing the keyword 'BLOCK'."""
    agent_name = callback_context.agent_name
    print(f"--- Callback: block_unsafe_content running for agent: {agent_name} ---")

    last_user_message_text = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == 'user' and content.parts:
                if content.parts[0].text:
                    last_user_message_text = content.parts[0].text
                    break

    if "BLOCK" in last_user_message_text.upper():
        print(f"--- Callback: Found 'BLOCK'. Blocking LLM call! ---")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I cannot process this request because it contains unsafe content.")],
            )
        )
    return None

def validate_tool_args(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """Validates tool arguments."""
    print(f"--- Callback: validate_tool_args running for tool '{tool.name}' ---")
    # Example: Prevent empty user_input for get_context
    if tool.name == "get_context":
        user_input = args.get("user_input", "")
        if not user_input.strip():
             return {
                "status": "error",
                "error_message": "Input cannot be empty."
            }
    return None
