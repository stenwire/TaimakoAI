"""
Tests for the analyze_sentiment tool.
Validates sentiment analysis functionality with various input scenarios.
"""
import pytest
import json
from unittest.mock import MagicMock, patch


class TestAnalyzeSentiment:
    """Test suite for analyze_sentiment tool functionality."""
    
    @pytest.fixture
    def mock_tool_context(self):
        """Create a mock ToolContext with default state."""
        context = MagicMock()
        context.state = {}
        return context
    
    @pytest.fixture
    def mock_tool_context_with_api_key(self):
        """Create a mock ToolContext with API key."""
        context = MagicMock()
        context.state = {"api_key": "test-api-key"}
        return context
    
    class TestKeywordBasedSentiment:
        """Tests for fallback keyword-based sentiment detection.
        
        The keyword fallback only triggers when api_key is set AND genai
        is available, but the Gemini call fails.
        """
        
        @pytest.fixture
        def mock_tool_context_with_key(self):
            """Context with API key to trigger Gemini path."""
            context = MagicMock()
            context.state = {"api_key": "test-api-key"}
            return context
        
        def test_negative_sentiment_detected(self, mock_tool_context_with_key):
            """Test that negative keywords trigger negative sentiment on Gemini failure."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                # Make Gemini raise an exception to trigger keyword fallback
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from importlib import reload
                import app.services.agent_system.tools as tools_module
                
                result = tools_module.analyze_sentiment(
                    user_text="I hate this terrible service!",
                    tool_context=mock_tool_context_with_key
                )
                
                data = json.loads(result)
                assert data["sentiment"] == "Negative"
                assert data["score"] >= 0.8
        
        def test_negative_keywords_angry(self, mock_tool_context_with_key):
            """Test angry keyword detection."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from app.services.agent_system.tools import analyze_sentiment
                
                result = analyze_sentiment(
                    user_text="I am so angry about this!",
                    tool_context=mock_tool_context_with_key
                )
                
                data = json.loads(result)
                assert data["sentiment"] == "Negative"
        
        def test_negative_keywords_scam(self, mock_tool_context_with_key):
            """Test scam keyword detection."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from app.services.agent_system.tools import analyze_sentiment
                
                result = analyze_sentiment(
                    user_text="This is a scam!",
                    tool_context=mock_tool_context_with_key
                )
                
                data = json.loads(result)
                assert data["sentiment"] == "Negative"
        
        def test_positive_sentiment_detected(self, mock_tool_context_with_key):
            """Test that positive keywords trigger positive sentiment on Gemini failure."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from app.services.agent_system.tools import analyze_sentiment
                
                result = analyze_sentiment(
                    user_text="I love this great service! Thanks!",
                    tool_context=mock_tool_context_with_key
                )
                
                data = json.loads(result)
                assert data["sentiment"] == "Positive"
                assert data["score"] >= 0.8
        
        def test_neutral_sentiment_without_api_key(self, mock_tool_context):
            """Test that without API key, sentiment is neutral (no Gemini, no fallback)."""
            from app.services.agent_system.tools import analyze_sentiment
            
            result = analyze_sentiment(
                user_text="Even with hate words, no api key = neutral",
                tool_context=mock_tool_context
            )
            
            data = json.loads(result)
            # Without api_key, Gemini path is not taken, so no fallback keywords
            assert data["sentiment"] == "Neutral"
            assert data["score"] == 0.5
    
    class TestStateManagement:
        """Tests for state storage behavior."""
        
        @pytest.fixture
        def mock_tool_context_with_key(self):
            """Context with API key."""
            context = MagicMock()
            context.state = {"api_key": "test-api-key"}
            return context
        
        def test_sentiment_stored_in_state(self, mock_tool_context_with_key):
            """Test that sentiment is stored in tool context state."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from app.services.agent_system.tools import analyze_sentiment
                
                analyze_sentiment(
                    user_text="This is terrible!",
                    tool_context=mock_tool_context_with_key
                )
                
                assert mock_tool_context_with_key.state["last_sentiment"] == "Negative"
        
        def test_positive_sentiment_stored(self, mock_tool_context_with_key):
            """Test that positive sentiment is stored correctly."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from app.services.agent_system.tools import analyze_sentiment
                
                analyze_sentiment(
                    user_text="I love this!",
                    tool_context=mock_tool_context_with_key
                )
                
                assert mock_tool_context_with_key.state["last_sentiment"] == "Positive"
        
        def test_neutral_sentiment_stored_without_api_key(self, mock_tool_context):
            """Test that neutral sentiment is stored when no api_key."""
            from app.services.agent_system.tools import analyze_sentiment
            
            analyze_sentiment(
                user_text="Any text here",
                tool_context=mock_tool_context
            )
            
            assert mock_tool_context.state["last_sentiment"] == "Neutral"
    
    class TestOutputFormat:
        """Tests for output format and structure."""
        
        @pytest.fixture
        def mock_tool_context(self):
            """Context without API key."""
            context = MagicMock()
            context.state = {}
            return context
        
        def test_output_is_valid_json(self, mock_tool_context):
            """Test that output is valid JSON."""
            from app.services.agent_system.tools import analyze_sentiment
            
            result = analyze_sentiment(
                user_text="Test message",
                tool_context=mock_tool_context
            )
            
            # Should not raise any exception
            data = json.loads(result)
            assert isinstance(data, dict)
        
        def test_output_contains_required_fields(self, mock_tool_context):
            """Test that output contains sentiment and score fields."""
            from app.services.agent_system.tools import analyze_sentiment
            
            result = analyze_sentiment(
                user_text="Test message",
                tool_context=mock_tool_context
            )
            
            data = json.loads(result)
            assert "sentiment" in data
            assert "score" in data
        
        def test_score_is_within_range(self, mock_tool_context):
            """Test that score is between 0.0 and 1.0."""
            from app.services.agent_system.tools import analyze_sentiment
            
            result = analyze_sentiment(
                user_text="Any text here",
                tool_context=mock_tool_context
            )
            
            data = json.loads(result)
            assert 0.0 <= data["score"] <= 1.0
    
    class TestInputValidation:
        """Tests for input validation."""
        
        @pytest.fixture
        def mock_tool_context(self):
            """Context without API key."""
            context = MagicMock()
            context.state = {}
            return context
        
        def test_empty_text_handled(self, mock_tool_context):
            """Test that empty text is handled (returns error or neutral)."""
            from app.services.agent_system.tools import analyze_sentiment
            
            result = analyze_sentiment(
                user_text="",
                tool_context=mock_tool_context
            )
            
            # Empty string should either error or return valid JSON
            if "Error" not in result:
                data = json.loads(result)
                assert "sentiment" in data
    
    class TestEdgeCases:
        """Tests for edge cases and boundary conditions."""
        
        @pytest.fixture
        def mock_tool_context_with_key(self):
            """Context with API key."""
            context = MagicMock()
            context.state = {"api_key": "test-api-key"}
            return context
        
        @pytest.fixture
        def mock_tool_context(self):
            """Context without API key."""
            context = MagicMock()
            context.state = {}
            return context
        
        def test_case_insensitive_keyword_detection(self, mock_tool_context_with_key):
            """Test that keyword detection is case insensitive."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from app.services.agent_system.tools import analyze_sentiment
                
                result = analyze_sentiment(
                    user_text="I HATE THIS!",
                    tool_context=mock_tool_context_with_key
                )
                
                data = json.loads(result)
                assert data["sentiment"] == "Negative"
        
        def test_mixed_signals_handled(self, mock_tool_context_with_key):
            """Test text with both positive and negative words."""
            with patch("app.services.agent_system.tools.genai") as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API Error")
                
                from app.services.agent_system.tools import analyze_sentiment
                
                result = analyze_sentiment(
                    user_text="I love the product but hate the service",
                    tool_context=mock_tool_context_with_key
                )
                
                data = json.loads(result)
                # First match is 'love' -> Negative comes second
                # Actually 'any' checks all, so first negative wins based on list order
                # The code checks negative keywords first
                assert data["sentiment"] in ["Positive", "Negative"]
        
        def test_unicode_text_handled(self, mock_tool_context):
            """Test that Unicode text is handled properly."""
            from app.services.agent_system.tools import analyze_sentiment
            
            result = analyze_sentiment(
                user_text="Мне нравится это! 我喜欢这个!",
                tool_context=mock_tool_context
            )
            
            data = json.loads(result)
            assert "sentiment" in data

