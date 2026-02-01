import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.agent_system.callbacks import trigger_session_analysis, _run_analysis_in_background
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types

# Use anyio marker for async tests (already installed)
pytestmark = pytest.mark.anyio

class TestAutomatedAnalysis:
    """Test suite for automated session analysis workflow."""
    
    async def test_analysis_callback_triggers(self):
        """Test that analysis callback fires when session_id is present."""
        # Mock callback context with session_id
        mock_context = Mock(spec=CallbackContext)
        mock_context.state = {
            "session_id": "test-session-123",
            "api_key": "test-api-key",
            "intents": ["Support", "Sales"]
        }
        
        # Mock LLM response
        mock_response = Mock(spec=LlmResponse)
        mock_response.content = types.Content(
            role="model",
            parts=[types.Part(text="Hello! How can I help you?")]
        )
        
        # Patch the background task creation
        with patch('asyncio.create_task') as mock_create_task:
            result = trigger_session_analysis(mock_context, mock_response)
            
            # Verify callback doesn't modify response
            assert result is None
            
            # Verify background task was created
            assert mock_create_task.called
            
    async def test_analysis_callback_no_session(self):
        """Test that analysis callback gracefully handles missing session_id."""
        # Mock callback context WITHOUT session_id
        mock_context = Mock(spec=CallbackContext)
        mock_context.state = {
            "api_key": "test-api-key"
        }
        
        mock_response = Mock(spec=LlmResponse)
        
        # Should return None and not crash
        result = trigger_session_analysis(mock_context, mock_response)
        assert result is None
    
    async def test_analysis_persists_to_db(self):
        """Test that analysis results are persisted to database."""
        from app.db.session import SessionLocal
        from app.models.chat_session import ChatSession
        from app.models.widget import GuestUser
        from app.services.analysis_agent import persist_analysis
        import uuid
        
        db = SessionLocal()
        
        try:
            # Create test guest user
            guest = GuestUser(
                id=str(uuid.uuid4()),
                widget_id=str(uuid.uuid4()),
                name="Test User"
            )
            db.add(guest)
            db.commit()
            
            # Create test session
            session = ChatSession(
                id=str(uuid.uuid4()),
                guest_id=guest.id
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            
            # Persist analysis
            test_summary = "User asked about product features"
            test_intent = "Support"
            
            updated_session = await persist_analysis(
                db, 
                session.id, 
                test_summary, 
                test_intent
            )
            
            # Verify persistence
            assert updated_session is not None
            assert updated_session.summary == test_summary
            assert updated_session.top_intent == test_intent
            assert updated_session.summary_generated_at is not None
            
        finally:
            # Cleanup
            db.query(ChatSession).filter(ChatSession.id == session.id).delete()
            db.query(GuestUser).filter(GuestUser.id == guest.id).delete()
            db.commit()
            db.close()
    
    async def test_analysis_non_blocking(self):
        """Test that analysis runs in background without blocking."""
        import time
        
        mock_context = Mock(spec=CallbackContext)
        mock_context.state = {
            "session_id": "test-session-async",
            "api_key": "test-key",
            "intents": ["General"]
        }
        
        mock_response = Mock(spec=LlmResponse)
        
        start_time = time.time()
        
        # Trigger analysis
        result = trigger_session_analysis(mock_context, mock_response)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should return immediately (< 100ms)
        assert elapsed < 0.1
        assert result is None
    
    async def test_analysis_error_graceful(self):
        """Test that analysis failures don't crash the agent."""
        # Mock context with invalid session_id
        mock_context = Mock(spec=CallbackContext)
        mock_context.state = {
            "session_id": "non-existent-session",
            "api_key": None,  # Missing API key
            "intents": None
        }
        
        mock_response = Mock(spec=LlmResponse)
        
        # Should not raise exception
        try:
            result = trigger_session_analysis(mock_context, mock_response)
            assert result is None  # Response should still be returned
        except Exception as e:
            pytest.fail(f"Analysis error should be handled gracefully, but raised: {e}")
    
    async def test_background_analysis_timeout(self):
        """Test that background analysis has timeout protection."""
        from app.db.session import SessionLocal
        
        # Mock analyze_session to take too long
        async def slow_analysis(*args, **kwargs):
            await asyncio.sleep(15)  # Longer than 10s timeout
            return "Summary", "Intent"
        
        with patch('app.services.analysis_agent.analyze_session', side_effect=slow_analysis):
            # Should timeout and not crash
            try:
                await _run_analysis_in_background(
                    session_id="test-session",
                    api_key="test-key",
                    intents=["Support"]
                )
                # If we get here, timeout was handled
            except asyncio.TimeoutError:
                pytest.fail("Timeout should be handled internally")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
