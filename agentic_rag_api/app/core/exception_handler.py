from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from app.core.response_wrapper import error_response
from typing import Union


def get_error_code(status_code: int) -> str:
    """Map HTTP status codes to error codes."""
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return error_code_map.get(status_code, "UNKNOWN_ERROR")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Global handler for HTTPException to ensure all errors use standardized response format.
    """
    error_code = get_error_code(exc.status_code)
    
    # Extract detail message
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    
    return error_response(
        message=detail,
        error_code=error_code,
        status_code=exc.status_code
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for request validation errors (422).
    """
    # Format validation errors into a readable message
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    error_message = "Validation error: " + "; ".join(errors)
    
    return error_response(
        message=error_message,
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        data={"errors": exc.errors()}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    """
    # Log the exception here in production
    import traceback
    traceback.print_exc()
    
    return error_response(
        message="An unexpected error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
