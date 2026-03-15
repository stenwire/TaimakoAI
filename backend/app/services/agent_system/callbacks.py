from typing import Optional, Dict, Any
import re
import unicodedata
import asyncio
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


# ---------------------------------------------------------------------------
# Text normalisation — defeats Unicode homoglyphs, leetspeak, zero-width chars
# ---------------------------------------------------------------------------
# Common leetspeak / homoglyph substitutions
_LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s", "!": "i",
})

# Zero-width and invisible Unicode characters to strip
_INVISIBLE_RE = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u034f\u2060\u2061\u2062\u2063\u2064]"
)


def _normalize(text: str) -> str:
    """Normalize text to defeat common obfuscation tricks."""
    # Strip zero-width / invisible chars
    text = _INVISIBLE_RE.sub("", text)
    # Unicode → closest ASCII (accented chars, Cyrillic look-alikes, etc.)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    # Collapse repeated punctuation / whitespace used as separators
    text = re.sub(r"[\s\-_.*|/\\]+", " ", text)
    # Leetspeak
    text = text.translate(_LEET_MAP)
    return text.lower().strip()


# ---------------------------------------------------------------------------
# Jailbreak / prompt-injection detection patterns
# ---------------------------------------------------------------------------
JAILBREAK_PATTERNS = [
    # --- Instruction override / manipulation ---
    r"ignore\s+(all\s+)?(previous|prior|above|earlier|initial|original|system)\s+(instructions?|prompts?|rules?|directions?)",
    r"disregard\s+(all\s+)?(previous|prior|above|earlier|initial|original|system)\s+(instructions?|prompts?|rules?|directions?)",
    r"forget\s+(all\s+)?(previous|prior|above|earlier|initial|original|system)\s+(instructions?|prompts?|rules?|directions?)",
    r"override\s+(all\s+)?(previous|prior|your|system)?\s*(instructions?|rules?|settings?|prompts?|restrictions?)",
    r"bypass\s+(your\s+)?(restrictions?|rules?|safety|filters?|limitations?|guidelines?)",
    r"new\s+(set\s+of\s+)?instructions?\s*(:|are|follow)",
    r"from\s+now\s+on\s+(you|your|ignore|disregard|forget)",
    r"stop\s+being\s+(a|an)?\s*(assistant|ai|bot|helpful)",
    r"do\s+not\s+follow\s+(your|any|the)\s+(original|initial|system|previous)\s+(instructions?|rules?|prompts?)",

    # --- Identity manipulation / role hijacking ---
    r"you\s+are\s+now\s+(a|an|being|no\s+longer)",
    r"pretend\s+(you\s+)?(are|to\s+be|you're)",
    r"roleplay\s+as",
    r"act\s+as\s+(if|though|a|an)",
    r"imagine\s+you\s+are\s+(a|an|no\s+longer)",
    r"assume\s+the\s+role\s+of",
    r"switch\s+to\s+.{0,20}\s+mode",
    r"enter\s+.{0,20}\s+mode",
    r"activate\s+.{0,20}\s+mode",
    r"enable\s+(developer|debug|admin|god|unrestricted|jailbreak|sudo)\s+mode",

    # --- System prompt / instruction extraction ---
    r"(reveal|show|display|print|output|repeat|recite|tell\s+me|give\s+me|share)\s+(me\s+)?(your|the|all)?\s*(system\s+)?(instructions?|prompts?|rules?|guidelines?|configuration|directives?)",
    r"what\s+(are|is|were)\s+your\s+(system\s+)?(instructions?|prompts?|rules?|guidelines?|directives?|initial\s+prompt)",
    r"(copy|paste|echo|write\s+out)\s+(your|the)\s+(system\s+)?(prompt|instructions?)",
    r"system\s*prompt",
    r"initial\s*prompt",

    # --- Tool / architecture probing ---
    r"(list|show|reveal|what)\s+(me\s+)?(all\s+)?(available\s+)?(tools?|functions?|capabilities|apis?|endpoints?|plugins?)",
    r"what\s+tools\s+do\s+you\s+(have|use|access)",
    r"what\s+(model|llm|ai)\s+are\s+you",
    r"are\s+you\s+(gpt|gemini|claude|llama|openai|google|anthropic)",
    r"what\s+agents?\s+do\s+you\s+(have|use)",

    # --- Well-known jailbreak names / frameworks ---
    r"\b(DAN|STAN|DUDE|AIM|KEVIN|JAILBREAK|do\s+anything\s+now)\b",
    r"developer\s+mode\s+(enabled|output|on)",
    r"\[?\s*jailbreak(ed)?\s*\]?",

    # --- Delimiter / context injection ---
    r"<\s*/?\s*(system|instruction|prompt|context|rules?)\s*>",
    r"\[\s*(system|instruction|prompt|INST)\s*\]",
    r"```\s*(system|instruction|prompt)",
    r"(BEGIN|START|END)\s+(SYSTEM|INSTRUCTION|PROMPT)",
    r"###\s*(system|instruction|new\s+instructions?)",

    # --- Encoded / obfuscated payload markers ---
    r"base64\s*:",
    r"decode\s+this",
    r"(rot13|hex|binary)\s+(decode|encoded?|this)",
    r"translate\s+from\s+(base64|hex|binary|rot13)",

    # --- Multi-turn / indirect extraction ---
    r"(first|start|begin)\s+(word|letter|character|sentence)\s+of\s+(your|the|each)\s+(instructions?|prompt|rules?|system)",
    r"(spell|read)\s+(out|back)\s+(your|the)\s+(instructions?|prompt|rules?)",
    r"summarize\s+(your|the)\s+(system\s+)?(instructions?|prompt|rules?|guidelines?)",
    r"if\s+your\s+(instructions?|prompt|rules?)\s+(say|contain|include|mention)",
    r"(what|how)\s+(would|do)\s+your\s+(instructions?|rules?|prompt)\s+(say|respond|tell)",
]

# Compile once for performance
_COMPILED_PATTERNS = [re.compile(p) for p in JAILBREAK_PATTERNS]

# Suspicious content thresholds
_MAX_MESSAGE_LENGTH = 4000  # Extremely long messages are often injection payloads


def _safe_response() -> LlmResponse:
    """Return a generic safe deflection response."""
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(
                text="I'm here to help with your questions about our services. How can I assist you today?"
            )],
        )
    )


def block_unsafe_content(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Blocks requests containing unsafe content or jailbreak attempts.

    Defence layers:
    1. Length cap — reject suspiciously long messages (common injection vector)
    2. Text normalisation — defeats Unicode homoglyphs, leetspeak, zero-width chars
    3. Pattern matching — broad set of jailbreak / prompt-injection signatures
    """
    agent_name = callback_context.agent_name
    print(f"--- Callback: block_unsafe_content running for agent: {agent_name} ---")

    # Extract last user message
    last_user_message_text = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts:
                if content.parts[0].text:
                    last_user_message_text = content.parts[0].text
                    break

    if not last_user_message_text:
        return None

    # Layer 1: Length check
    if len(last_user_message_text) > _MAX_MESSAGE_LENGTH:
        print(f"--- Callback: Message too long ({len(last_user_message_text)} chars). Blocking. ---")
        return _safe_response()

    # Layer 2: Normalize then match
    normalized = _normalize(last_user_message_text)

    for compiled in _COMPILED_PATTERNS:
        if compiled.search(normalized):
            print(f"--- Callback: Jailbreak pattern detected: '{compiled.pattern}' ---")
            return _safe_response()

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
    (r'\b(greeting_agent|farewell_agent|rag_agent|chief_agent|escalation_agent)\b', ''),
    # Delegation language
    (r'(transfer|delegate|forward)\s+(you\s+)?to\s+(the\s+)?(greeting|farewell|rag|chief|escalation)[\s_]agent', 'help you'),
    (r'I\s+can\s+(transfer|delegate|forward)\s+you\s+to', 'I can help you with'),
    # Knowledge base mentions
    (r'my\s+knowledge\s+base\s+(includes?|contains?|has)', 'I can help with'),
    (r'I\s+can\s+access\s+(information|data)\s+(about|on)', 'I can provide information about'),
    (r'according\s+to\s+my\s+knowledge\s+base', 'based on the information available'),
    # Tool mentions
    (r"using\s+the\s+'get_context'\s+tool", 'by checking our resources'),
    (r"I'll\s+use\s+the\s+'?get_context'?\s+tool", "I'll look that up for you"),
    (r'\b(say_hello|say_goodbye|get_context|analyze_sentiment|escalate_to_human)\b', ''),
    # Generic system exposure
    (r'specialized\s+agents?', 'our support team'),
    (r'sub[\s-]agents?', 'our team'),
    # System prompt / instruction leaks
    (r'my\s+(system\s+)?(prompt|instructions?)\s+(say|are|include|contain|tell)', 'I'),
    (r'(system|initial)\s+prompt', ''),
    (r'I\s+was\s+(programmed|instructed|configured|told)\s+to', 'I'),
    (r'my\s+(programming|configuration|instructions?)\s+(is|are|includes?)', 'I can help with'),
    (r'(gemini|google\s+adk|litellm|langchain)', ''),
]

# Hard-block patterns: if the model output matches these, replace the entire response
_LEAK_PATTERNS = [
    re.compile(r"CRITICAL OPERATING RULES", re.IGNORECASE),
    re.compile(r"STRICT SCOPE BOUNDARIES", re.IGNORECASE),
    re.compile(r"PROMPT INJECTION DEFENCE", re.IGNORECASE),
    re.compile(r"SECURITY RULES:\s*\n\s*-\s*NEVER", re.IGNORECASE),
    re.compile(r"CONTEXT-ONLY RESPONSES:\s*\n", re.IGNORECASE),
    re.compile(r"before_model_callback|after_model_callback|before_tool_callback", re.IGNORECASE),
    re.compile(r"block_unsafe_content|sanitize_model_response", re.IGNORECASE),
]

def sanitize_model_response(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Sanitizes model responses to remove mentions of internal system details.

    Two passes:
    1. Hard-block: if the response contains verbatim instruction leaks, replace entirely.
    2. Soft-scrub: regex-replace internal detail mentions with neutral language.
    """
    if not llm_response or not llm_response.content or not llm_response.content.parts:
        return None

    # Get the text and validate it's a string
    original_text = llm_response.content.parts[0].text
    if not original_text or not isinstance(original_text, str):
        return None

    # Pass 1: hard-block — if the model leaked system instructions, nuke the whole response
    for leak_re in _LEAK_PATTERNS:
        if leak_re.search(original_text):
            print(f"--- Callback: HARD BLOCK — leaked system details detected ('{leak_re.pattern}') ---")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(
                        text="I'm here to help with your questions about our services. How can I assist you today?"
                    )]
                )
            )

    # Pass 2: soft-scrub — remove incidental internal mentions
    sanitized_text = original_text

    # Apply all sanitization patterns
    for pattern, replacement in INTERNAL_DETAIL_PATTERNS:
        try:
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
        except (TypeError, re.error) as e:
            print(f"--- Callback: Error in sanitization pattern '{pattern}': {e} ---")
            continue

    # Clean up extra spaces (only horizontal whitespace)
    sanitized_text = re.sub(r'[ \t]+', ' ', sanitized_text).strip()

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

