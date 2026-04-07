"""Unit tests for app.core.response_wrapper module.

Tests the success_response() and error_response() helper functions that
provide the standardized API response envelope: {status, message, data, error_code}.
"""

import json
import pytest
from fastapi import status as http_status

from app.core.response_wrapper import success_response, error_response, APIResponse


@pytest.mark.unit
class TestSuccessResponse:
    """Tests for the success_response() helper."""

    def test_success_response_default_message(self):
        """Default message should be 'Success'."""
        resp = success_response()
        body = json.loads(resp.body)
        assert body["message"] == "Success"

    def test_success_response_default_status_code(self):
        """Default HTTP status code should be 200."""
        resp = success_response()
        assert resp.status_code == http_status.HTTP_200_OK

    def test_success_response_status_field_is_success(self):
        """The 'status' field in the JSON body should be 'success'."""
        resp = success_response()
        body = json.loads(resp.body)
        assert body["status"] == "success"

    def test_success_response_data_is_none_by_default(self):
        """When no data is passed, the 'data' field should be None."""
        resp = success_response()
        body = json.loads(resp.body)
        assert body["data"] is None

    def test_success_response_with_data(self):
        """Passed data should appear in the 'data' field."""
        payload = {"id": 1, "name": "test"}
        resp = success_response(data=payload)
        body = json.loads(resp.body)
        assert body["data"] == payload

    def test_success_response_with_custom_message(self):
        """Custom message should override the default."""
        resp = success_response(message="Created successfully")
        body = json.loads(resp.body)
        assert body["message"] == "Created successfully"

    def test_success_response_with_custom_status_code(self):
        """Custom status_code should be reflected in the HTTP response."""
        resp = success_response(status_code=http_status.HTTP_201_CREATED)
        assert resp.status_code == 201

    def test_success_response_error_code_is_none(self):
        """Success responses should have error_code as None."""
        resp = success_response()
        body = json.loads(resp.body)
        assert body["error_code"] is None

    def test_success_response_with_list_data(self):
        """success_response should handle list data correctly."""
        data = [{"id": 1}, {"id": 2}]
        resp = success_response(data=data)
        body = json.loads(resp.body)
        assert body["data"] == data


@pytest.mark.unit
class TestErrorResponse:
    """Tests for the error_response() helper."""

    def test_error_response_status_field_is_error(self):
        """The 'status' field in the JSON body should be 'error'."""
        resp = error_response(message="Something went wrong")
        body = json.loads(resp.body)
        assert body["status"] == "error"

    def test_error_response_default_status_code(self):
        """Default HTTP status code should be 400 Bad Request."""
        resp = error_response(message="Bad input")
        assert resp.status_code == http_status.HTTP_400_BAD_REQUEST

    def test_error_response_message_is_set(self):
        """The provided message should appear in the response."""
        resp = error_response(message="Validation failed")
        body = json.loads(resp.body)
        assert body["message"] == "Validation failed"

    def test_error_response_error_code_none_by_default(self):
        """error_code should be None when not provided."""
        resp = error_response(message="Error")
        body = json.loads(resp.body)
        assert body["error_code"] is None

    def test_error_response_with_custom_error_code(self):
        """Custom error_code should be included in the response."""
        resp = error_response(message="Auth failed", error_code="AUTH_EXPIRED")
        body = json.loads(resp.body)
        assert body["error_code"] == "AUTH_EXPIRED"

    def test_error_response_with_custom_status_code(self):
        """Custom HTTP status code should be reflected."""
        resp = error_response(
            message="Not found",
            status_code=http_status.HTTP_404_NOT_FOUND,
        )
        assert resp.status_code == 404

    def test_error_response_data_is_none_by_default(self):
        """data should be None when not provided."""
        resp = error_response(message="Error")
        body = json.loads(resp.body)
        assert body["data"] is None

    def test_error_response_with_data(self):
        """When data is provided it should appear in the response."""
        extra = {"field": "email", "issue": "invalid"}
        resp = error_response(message="Validation error", data=extra)
        body = json.loads(resp.body)
        assert body["data"] == extra


@pytest.mark.unit
class TestAPIResponseModel:
    """Tests for the APIResponse Pydantic model."""

    def test_api_response_required_fields(self):
        """APIResponse requires status and message."""
        model = APIResponse(status="success", message="ok")
        assert model.status == "success"
        assert model.message == "ok"

    def test_api_response_optional_fields_default_none(self):
        """data and error_code should default to None."""
        model = APIResponse(status="error", message="fail")
        assert model.data is None
        assert model.error_code is None
