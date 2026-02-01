"""
Tests for the say_goodbye tool.
Validates farewell functionality and output format.
"""
import pytest
from app.services.agent_system.tools import say_goodbye


class TestSayGoodbye:
    """Test suite for say_goodbye tool functionality."""
    
    class TestBasicFarewell:
        """Tests for basic farewell behavior."""
        
        def test_farewell_message_returned(self):
            """Test that calling say_goodbye returns a farewell message."""
            result = say_goodbye()
            
            assert "Goodbye" in result
            assert "great day" in result.lower()
        
        def test_farewell_is_polite(self):
            """Test that farewell message is friendly and polite."""
            result = say_goodbye()
            
            # Should contain positive sentiment
            assert any(word in result.lower() for word in ["great", "good", "nice", "have"])
    
    class TestOutputFormat:
        """Tests for output format and structure."""
        
        def test_output_is_string(self):
            """Test that output is always a string."""
            result = say_goodbye()
            
            assert isinstance(result, str)
        
        def test_output_not_empty(self):
            """Test that output is never empty."""
            result = say_goodbye()
            
            assert len(result) > 0
            assert result.strip() != ""
        
        def test_output_is_consistent(self):
            """Test that repeated calls return consistent message."""
            result1 = say_goodbye()
            result2 = say_goodbye()
            
            # Should always return the same farewell message
            assert result1 == result2
    
    class TestSchemaValidation:
        """Tests for schema compliance."""
        
        def test_no_parameters_required(self):
            """Test that function works without any parameters."""
            # Should not raise any exception
            result = say_goodbye()
            assert result is not None
        
        def test_farewell_output_matches_schema(self):
            """Test that output conforms to FarewellOutput schema."""
            from app.services.agent_system.tool_schemas import FarewellOutput
            
            result = say_goodbye()
            
            # Should be able to create a valid FarewellOutput with this message
            output = FarewellOutput(message=result)
            assert output.message == result
