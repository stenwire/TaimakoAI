from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import status

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None

def success_response(
    data: Any = None, 
    message: str = "Success", 
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    Returns a standardized success response.
    """
    content = APIResponse(
        status="success",
        message=message,
        data=data
    ).model_dump(mode='json')
    return JSONResponse(content=content, status_code=status_code)

def error_response(
    message: str, 
    error_code: Optional[str] = None, 
    status_code: int = status.HTTP_400_BAD_REQUEST,
    data: Any = None
) -> JSONResponse:
    """
    Returns a standardized error response.
    """
    content = APIResponse(
        status="error",
        message=message,
        error_code=error_code,
        data=data
    ).model_dump(mode='json')
    return JSONResponse(content=content, status_code=status_code)
