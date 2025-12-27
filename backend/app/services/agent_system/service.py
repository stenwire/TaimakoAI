from google.adk.sessions import DatabaseSessionService
from app.db.session import SQLALCHEMY_DATABASE_URL

# --- Session Management ---
# Using DatabaseSessionService for persistent session storage
session_service = DatabaseSessionService(db_url=SQLALCHEMY_DATABASE_URL)

async def init_session(app_name: str, user_id: str, session_id: str, initial_state: dict = None):
    """
    Initialize a session with optional initial state.
    Uses get-or-create pattern to avoid duplicate key errors.
    
    Args:
        app_name: Application/business name
        user_id: User identifier
        session_id: Session identifier
        initial_state: Optional initial state dictionary
        
    Returns:
        Existing or newly created session
    """
    if initial_state is None:
        initial_state = {}
    
    # Ensure user_id is in state for tools to access
    initial_state["user_id"] = user_id
    
    # Try to get existing session first
    try:
        existing_session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        if existing_session:
            # Session already exists, return it
            return existing_session
    except Exception:
        # Session doesn't exist or error occurred, will create new one
        pass
    
    # Create new session only if it doesn't exist
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state
    )
    print(f"Session created: App='{app_name}', User='{user_id}', Session='{session_id}'")
    return session
