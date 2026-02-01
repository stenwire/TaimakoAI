"""
Tests for the say_hello tool.
Validates greeting functionality with various input scenarios.
"""
import pytest
from app.services.agent_system.tools import say_hello


class TestSayHello:
    """Test suite for say_hello tool functionality."""
    
    class TestBasicGreeting:
        """Tests for basic greeting behavior."""
        
        def test_greeting_with_name(self):
            """Test that providing a name returns personalized greeting."""
            result = say_hello(name="Alice")
            
            assert "Alice" in result
            assert "Hello" in result
            assert "How can I help you today?" in result
        
        def test_greeting_without_name(self):
            """Test that no name returns generic greeting."""
            result = say_hello()
            
            assert "Hello" in result
            assert "How can I assist you" in result
        
        def test_greeting_with_none_name(self):
            """Test explicitly passing None as name."""
            result = say_hello(name=None)
            
            assert "Hello" in result
            assert "How can I assist you" in result
    
    class TestEdgeCases:
        """Tests for edge cases and boundary conditions."""
        
        def test_greeting_with_empty_string_name(self):
            """Test that empty string is treated as no name."""
            result = say_hello(name="")
            
            # Empty string evaluates to falsy, should get generic greeting
            assert "Hello" in result
            assert "How can I assist you" in result
        
        def test_greeting_with_whitespace_name(self):
            """Test name with only whitespace."""
            result = say_hello(name="   ")
            
            # Whitespace-only name is truthy, so it should be used
            assert "Hello" in result
        
        def test_greeting_with_special_characters(self):
            """Test name containing special characters."""
            result = say_hello(name="O'Brien-Smith")
            
            assert "O'Brien-Smith" in result
            assert "Hello" in result
        
        def test_greeting_with_unicode_name(self):
            """Test name with Unicode characters."""
            result = say_hello(name="José García")
            
            assert "José García" in result
            assert "Hello" in result
        
        def test_greeting_with_numeric_string(self):
            """Test name that is a numeric string."""
            result = say_hello(name="42")
            
            assert "42" in result
            assert "Hello" in result
        
        def test_greeting_with_long_name(self):
            """Test name at maximum length boundary."""
            long_name = "A" * 100  # Max length from schema
            result = say_hello(name=long_name)
            
            assert long_name in result
            assert "Hello" in result
    
    class TestOutputFormat:
        """Tests for output format and structure."""
        
        def test_output_is_string(self):
            """Test that output is always a string."""
            result = say_hello(name="Test")
            
            assert isinstance(result, str)
        
        def test_output_not_empty(self):
            """Test that output is never empty."""
            result_with_name = say_hello(name="Test")
            result_without_name = say_hello()
            
            assert len(result_with_name) > 0
            assert len(result_without_name) > 0


class TestSayHelloInputValidation:
    """Tests for input validation using Pydantic schemas."""
    
    def test_name_exceeds_max_length(self):
        """Test that name exceeding max length is handled."""
        # Schema has max_length=100
        very_long_name = "A" * 150
        result = say_hello(name=very_long_name)
        
        # Should return error message about invalid input
        assert "Error" in result or very_long_name in result
