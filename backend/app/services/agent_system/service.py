from app.db.session import SQLALCHEMY_DATABASE_URL, SessionLocal
from google.adk.sessions import DatabaseSessionService
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
import json

# --- Session Management ---
# Using DatabaseSessionService for persistent session storage
session_service = DatabaseSessionService(db_url=SQLALCHEMY_DATABASE_URL)


def _update_session_raw(app_name: str, user_id: str, session_id: str, state: dict):
    """
    Directly updates the session state in the database using raw SQL.
    This is necessary because DatabaseSessionService does not expose an update method.
    """
    try:
        db = SessionLocal()
        try:
            # Construct JSON string for state
            state_json = json.dumps(state)
            
            # Update query - targeting the specific session
            query = text("""
                UPDATE sessions 
                SET state = :state, update_time = now()
                WHERE app_name = :app_name AND user_id = :user_id AND id = :session_id
            """)
            
            db.execute(query, {
                "state": state_json,
                "app_name": app_name,
                "user_id": user_id,
                "session_id": session_id
            })
            db.commit()
            print(f"Session updated (Raw SQL): {session_id}")
        finally:
            db.close()
    except Exception as e:
        print(f"Error updating session via raw SQL: {e}")

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
            # Session exists, update its state with the new initial_state (e.g. new API key)
            if initial_state:
                _update_session_raw(app_name, user_id, session_id, initial_state)
            return existing_session
    except Exception as e:
        print(f"Error checking/updating session: {e}")
        # Session doesn't exist or error occurred, will create new one
        pass
    
    # Create new session only if it doesn't exist
    try:
        session = await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=initial_state
        )
        print(f"Session created: App='{app_name}', User='{user_id}', Session='{session_id}'")
        return session
    except IntegrityError:
        print(f"Session already exists (IntegrityError for {session_id}), attempting update...")
        # Fallback: session exists, so update it.
        # Note: We assume session_id collision means it's the same session.
        if initial_state:
            _update_session_raw(app_name, user_id, session_id, initial_state)
        # Fetch it again to return it
        return await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )

