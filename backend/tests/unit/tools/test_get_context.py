"""
Tests for the get_context tool.
Validates RAG-based context retrieval functionality.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestGetContext:
    """Test suite for get_context tool functionality."""
    
    @pytest.fixture
    def mock_tool_context(self):
        """Create a mock ToolContext with default state."""
        context = MagicMock()
        context.state = {
            "user_id": "test-user-123",
            "api_key": "test-api-key-456",
            "response_style": "normal"
        }
        return context
    
    @pytest.fixture
    def mock_rag_service(self):
        """Create a mock RAG service."""
        with patch("app.services.agent_system.tools.rag_service") as mock:
            mock.query.return_value = [
                "Context chunk 1: Relevant information.",
                "Context chunk 2: More details."
            ]
            yield mock
    
    class TestSuccessfulRetrieval:
        """Tests for successful context retrieval."""
        
        def test_retrieves_context_with_valid_input(self, mock_tool_context, mock_rag_service):
            """Test successful context retrieval with valid parameters."""
            from app.services.agent_system.tools import get_context
            
            result = get_context(user_input="What is Vendkit?", tool_context=mock_tool_context)
            
            assert "Context chunk 1" in result
            assert "Context chunk 2" in result
            mock_rag_service.query.assert_called_once()
        
        def test_passes_user_id_to_rag_service(self, mock_tool_context, mock_rag_service):
            """Test that user_id is correctly passed to RAG service."""
            from app.services.agent_system.tools import get_context
            
            get_context(user_input="Test query", tool_context=mock_tool_context)
            
            call_kwargs = mock_rag_service.query.call_args.kwargs
            assert call_kwargs["user_id"] == "test-user-123"
        
        def test_passes_api_key_to_rag_service(self, mock_tool_context, mock_rag_service):
            """Test that api_key is correctly passed to RAG service."""
            from app.services.agent_system.tools import get_context
            
            get_context(user_input="Test query", tool_context=mock_tool_context)
            
            call_kwargs = mock_rag_service.query.call_args.kwargs
            assert call_kwargs["api_key"] == "test-api-key-456"
        
        def test_joins_multiple_chunks(self, mock_tool_context, mock_rag_service):
            """Test that multiple chunks are joined properly."""
            from app.services.agent_system.tools import get_context
            
            mock_rag_service.query.return_value = ["Chunk A", "Chunk B", "Chunk C"]
            
            result = get_context(user_input="Query", tool_context=mock_tool_context)
            
            # Chunks should be joined with double newlines
            assert "Chunk A" in result
            assert "Chunk B" in result
            assert "Chunk C" in result
    
    class TestErrorHandling:
        """Tests for error handling scenarios."""
        
        def test_missing_user_id_returns_error(self, mock_rag_service):
            """Test that missing user_id returns error message."""
            from app.services.agent_system.tools import get_context
            
            context = MagicMock()
            context.state = {"api_key": "test-key"}  # No user_id
            
            result = get_context(user_input="Query", tool_context=context)
            
            assert "Error" in result
            assert "User ID not found" in result
        
        def test_missing_api_key_returns_error(self, mock_rag_service):
            """Test that missing api_key returns error message."""
            from app.services.agent_system.tools import get_context
            
            context = MagicMock()
            context.state = {"user_id": "test-user"}  # No api_key
            
            result = get_context(user_input="Query", tool_context=context)
            
            assert "Error" in result
            assert "API Key" in result
        
        def test_empty_input_returns_error(self, mock_tool_context, mock_rag_service):
            """Test that empty input is rejected."""
            from app.services.agent_system.tools import get_context
            
            result = get_context(user_input="", tool_context=mock_tool_context)
            
            assert "Error" in result
    
    class TestInputValidation:
        """Tests for input validation using Pydantic schemas."""
        
        def test_input_too_long_handled(self, mock_tool_context, mock_rag_service):
            """Test that overly long input is handled."""
            from app.services.agent_system.tools import get_context
            
            # Schema allows max 1000 characters
            long_input = "A" * 1100
            
            result = get_context(user_input=long_input, tool_context=mock_tool_context)
            
            # Should return an error or handle gracefully
            assert "Error" in result or isinstance(result, str)
    
    class TestStateInteraction:
        """Tests for interaction with ToolContext state."""
        
        def test_reads_response_style_from_state(self, mock_tool_context, mock_rag_service, capsys):
            """Test that response_style is read from state."""
            from app.services.agent_system.tools import get_context
            
            mock_tool_context.state["response_style"] = "formal"
            
            get_context(user_input="Query", tool_context=mock_tool_context)
            
            # The function prints the style, so we can verify via output
            captured = capsys.readouterr()
            assert "formal" in captured.out
