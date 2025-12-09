from google.adk.sessions import InMemorySessionService

# --- Session Management ---
session_service = InMemorySessionService()

async def init_session(app_name: str, user_id: str, session_id: str, initial_state: dict = None) -> InMemorySessionService:
    """
    Initialize a session with optional initial state.
    
    Args:
        app_name: Application/business name
        user_id: User identifier
        session_id: Session identifier
        initial_state: Optional initial state dictionary
        
    Returns:
        Created session
    """
    if initial_state is None:
        initial_state = {}
    
    # Ensure user_id is in state for tools to access
    initial_state["user_id"] = user_id
    
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state
    )
    print(f"Session created: App='{app_name}', User='{user_id}', Session='{session_id}'")
    return session

