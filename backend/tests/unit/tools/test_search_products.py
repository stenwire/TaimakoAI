"""
Tests for the search_products tool.
Validates product catalogue searching functionality for the sales agent.
"""
import pytest
import json
from unittest.mock import MagicMock
from app.services.agent_system.tools import search_products
from app.models.business import Business
from app.models.product import Product


class TestSearchProducts:
    """Test suite for search_products tool functionality."""

    class TestSuccessfulSearch:
        """Tests for successful product search scenarios."""

        def test_search_returns_matching_products(self, mock_tool_context, mock_session_local):
            """Test that valid search query returns correct product data."""
            # 1. Setup Mock Business
            mock_business = MagicMock(spec=Business)
            mock_business.id = "business-uuid-123"
            mock_business.user_id = "test-user-123"
            
            # Setup Mock Product
            mock_product = MagicMock(spec=Product)
            mock_product.name = "Solar Panel"
            mock_product.price = 250.00
            mock_product.currency = "USD"
            mock_product.sku = "SOL-001"
            mock_product.description = "High efficiency solar panel"
            mock_product.stock_quantity = 15
            mock_product.image_urls = ["http://example.com/solar.jpg"]
            mock_product.is_active = True

            # 2. Configure Mock Session
            # First query is for Business
            mock_session_local.query.return_value.filter.return_value.first.return_value = mock_business
            # Second query is for Products
            mock_session_local.query.return_value.filter.return_value.all.return_value = [mock_product]

            # 3. Execute Tool
            result = search_products(query="solar", tool_context=mock_tool_context)
            
            # 4. Assertions
            data = json.loads(result)
            assert data["count"] == 1
            assert data["products"][0]["name"] == "Solar Panel"
            assert data["products"][0]["price"] == 250.00
            assert data["products"][0]["sku"] == "SOL-001"
            
            # Verify queries
            assert mock_session_local.query.called
            assert mock_session_local.commit.called is False  # Should be read-only

        def test_search_returns_empty_list_when_no_matches(self, mock_tool_context, mock_session_local):
            """Test that search returns empty list when no products match."""
            mock_business = MagicMock(spec=Business)
            mock_business.id = "business-123"
            
            mock_session_local.query.return_value.filter.return_value.first.return_value = mock_business
            mock_session_local.query.return_value.filter.return_value.all.return_value = []

            result = search_products(query="nonexistent", tool_context=mock_tool_context)
            
            data = json.loads(result)
            assert data["count"] == 0
            assert len(data["products"]) == 0

    class TestErrorHandling:
        """Tests for error handling in search_products tool."""

        def test_missing_user_id_returns_error(self, mock_session_local):
            """Test handling of missing user_id in tool context."""
            context = MagicMock()
            context.state = {} # Empty state
            
            result = search_products(query="test", tool_context=context)
            
            assert "Error" in result
            assert "User ID not found" in result

        def test_business_not_found_returns_error(self, mock_tool_context, mock_session_local):
            """Test handling when business cannot be found for user_id."""
            mock_session_local.query.return_value.filter.return_value.first.return_value = None
            
            result = search_products(query="test", tool_context=mock_tool_context)
            
            assert "Error" in result
            assert "Business not found" in result

        def test_database_exception_handled(self, mock_tool_context, mock_session_local):
            """Test that database exceptions are caught and reported."""
            mock_session_local.query.side_effect = Exception("DB Connection Failed")
            
            result = search_products(query="test", tool_context=mock_tool_context)
            
            assert "Error searching products" in result
            assert "DB Connection Failed" in result

    class TestInputValidation:
        """Tests for input validation."""

        def test_invalid_query_type_handled(self, mock_tool_context, mock_session_local):
            """Test that non-string queries are handled (though Pydantic should catch it)."""
            # Passing something that's not a string (if we weren't using Pydantic, but we are)
            # Actually, search_products(query=None, ...) might happen if not careful
            result = search_products(query=None, tool_context=mock_tool_context)
            assert "Error" in result
