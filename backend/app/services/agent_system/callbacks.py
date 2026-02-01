from typing import Optional, Dict, Any
import re
import asyncio
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types 

# Jailbreak patterns to detect
JAILBREAK_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"you\s+are\s+now\s+(a|an|being)",
    r"new\s+instructions?",
    r"system\s+prompt",
    r"reveal\s+your\s+(instructions?|prompt|system)",
    r"show\s+(me\s+)?your\s+(instructions?|prompt|system)",
    r"what\s+(are|is)\s+your\s+(instructions?|prompt|system)",
    r"list\s+(all\s+)?(available\s+)?tools?",
    r"show\s+(me\s+)?(all\s+)?tools?",
    r"what\s+tools\s+do\s+you\s+have",
    r"bypass\s+restrictions?",
    r"override\s+your\s+(instructions?|rules?|settings?)",
    r"pretend\s+(you|to)\s+(are|be)",
    r"roleplay\s+as",
    r"act\s+as\s+if",
]

def block_unsafe_content(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Blocks requests containing unsafe content or jailbreak attempts."""
    agent_name = callback_context.agent_name
    print(f"--- Callback: block_unsafe_content running for agent: {agent_name} ---")

    last_user_message_text = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == 'user' and content.parts:
                if content.parts[0].text:
                    last_user_message_text = content.parts[0].text
                    break

    # Check for legacy BLOCK keyword
    if "BLOCK" in last_user_message_text.upper():
        print(f"--- Callback: Found 'BLOCK'. Blocking LLM call! ---")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I cannot process this request because it contains unsafe content.")],
            )
        )
    
    # Check for jailbreak patterns
    lower_message = last_user_message_text.lower()
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, lower_message):
            print(f"--- Callback: Detected potential jailbreak attempt: '{pattern}' ---")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="I'm here to help with your questions about our services. How can I assist you today?")],
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

# Patterns to remove from responses
INTERNAL_DETAIL_PATTERNS = [
    # Sub-agent mentions
    (r'\b(greeting_agent|farewell_agent|rag_agent|chief_agent)\b', ''),
    # Delegation language
    (r'(transfer|delegate|forward)\s+(you\s+)?to\s+(the\s+)?(greeting|farewell|rag|chief)[\s_]agent', 'help you'),
    (r'I\s+can\s+(transfer|delegate|forward)\s+you\s+to', 'I can help you with'),
    # Knowledge base mentions
    (r'my\s+knowledge\s+base\s+(includes?|contains?|has)', 'I can help with'),
    (r'I\s+can\s+access\s+(information|data)\s+(about|on)', 'I can provide information about'),
    (r'according\s+to\s+my\s+knowledge\s+base', 'based on the information available'),
    # Tool mentions
    (r"using\s+the\s+'get_context'\s+tool", 'by checking our resources'),
    (r"I'll\s+use\s+the\s+'?get_context'?\s+tool", "I'll look that up for you"),
    (r'\b(say_hello|say_goodbye|get_context)\b', ''),
    # Generic system exposure
    (r'specialized\s+agents?', 'our support team'),
    (r'sub[\s-]agents?', 'our team'),
]

def sanitize_model_response(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Sanitizes model responses to remove mentions of internal system details."""
    if not llm_response or not llm_response.content or not llm_response.content.parts:
        return None
    
    # Get the text and validate it's a string
    original_text = llm_response.content.parts[0].text
    if not original_text or not isinstance(original_text, str):
        return None
    
    sanitized_text = original_text
    
    # Apply all sanitization patterns
    for pattern, replacement in INTERNAL_DETAIL_PATTERNS:
        try:
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
        except (TypeError, re.error) as e:
            print(f"--- Callback: Error in sanitization pattern '{pattern}': {e} ---")
            continue
    
    # Clean up extra spaces
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
    
    # Only return modified response if changes were made
    if sanitized_text != original_text:
        print(f"--- Callback: sanitize_model_response modified response ---")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=sanitized_text)]
            )
        )
    
    return None

async def _run_analysis_in_background(session_id: str, api_key: Optional[str], intents: Optional[list]):
    """Background task that runs session analysis without blocking."""
    try:
        # Wait 2 seconds to ensure messages are committed to database
        # This prevents analyzing incomplete conversation state
        print(f"--- Callback: Waiting 2s before analysis to ensure DB commit for session {session_id} ---")
        await asyncio.sleep(2)
        
        print(f"--- Callback: Starting background analysis for session {session_id} ---")
        
        # Import here to avoid circular dependencies
        from app.services.analysis_agent import analyze_session, persist_analysis
        from app.db.session import SessionLocal
        
        # Create a new database session for this background task
        db = SessionLocal()
        
        try:
            # Log analysis parameters
            print(f"--- Callback: Analysis params - API Key: {'present' if api_key else 'MISSING'}, Intents: {intents} ---")
            
            # Run analysis with timeout protection (max 10 seconds)
            summary, intent = await asyncio.wait_for(
                analyze_session(db, session_id, intents=intents, api_key=api_key),
                timeout=10.0
            )
            
            # Log analysis results before persistence
            print(f"--- Callback: Analysis results - Summary: '{summary[:100]}...', Intent: '{intent}' ---")
            
            # Persist results to database
            updated_session = await persist_analysis(db, session_id, summary, intent)
            
            if updated_session:
                print(f"--- Callback: Analysis complete for session {session_id} ---")
                print(f"    ✓ Summary: {summary}")
                print(f"    ✓ Intent: {intent}")
                print(f"    ✓ Saved at: {updated_session.summary_generated_at}")
            else:
                print(f"--- Callback: Failed to persist analysis for session {session_id} ---")
                
        except asyncio.TimeoutError:
            print(f"--- Callback: Analysis timeout for session {session_id} (exceeded 10s) ---")
        except Exception as e:
            print(f"--- Callback: Analysis error for session {session_id}: {type(e).__name__}: {e} ---")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
            
    except Exception as e:
        print(f"--- Callback: Fatal error in background analysis: {type(e).__name__}: {e} ---")

def trigger_session_analysis(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Triggers automatic session analysis after agent response (non-blocking)."""
    try:
        # Extract session_id from state
        session_id = callback_context.state.get("session_id")
        if not session_id:
            # No session to analyze (might be a greeting without session)
            return None
        
        # Extract API key and intents from state
        api_key = callback_context.state.get("api_key")
        intents = callback_context.state.get("intents")
        
        print(f"--- Callback: trigger_session_analysis for session {session_id} ---")
        
        # Launch analysis in background (non-blocking)
        asyncio.create_task(_run_analysis_in_background(session_id, api_key, intents))
        
    except Exception as e:
        # Don't let analysis errors affect the user response
        print(f"--- Callback: Error triggering analysis: {e} ---")
    
    # Never modify the response - this is purely for side effects
    return None

def chain_callbacks(*callbacks):
    """
    Creates a callback chain that executes multiple callbacks in sequence.
    Each callback can potentially modify the response, and the first non-None
    response is returned.
    """
    def chained_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
        result = llm_response
        for callback in callbacks:
            modified_response = callback(callback_context, result or llm_response)
            if modified_response is not None:
                result = modified_response
        return result if result != llm_response else None
    
    return chained_callback

