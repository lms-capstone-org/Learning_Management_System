"""
Standard API response format across the LMS
"""
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from enum import Enum


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: ResponseStatus = ResponseStatus.ERROR
    message: str
    code: str
    timestamp: str
    path: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Standard success response"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str
    data: Optional[Any] = None
    timestamp: str


class PaginatedResponse(BaseModel):
    """Paginated response"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str
    data: List[Any]
    pagination: Dict[str, int]  # {total, page, per_page, pages}
    timestamp: str


def format_error(
    message: str,
    code: str,
    path: str = None,
    details: dict = None
) -> Dict[str, Any]:
    """Format error response"""
    from datetime import datetime
    return {
        "status": "error",
        "message": message,
        "code": code,
        "timestamp": datetime.utcnow().isoformat(),
        "path": path,
        "details": details
    }


def format_success(
    message: str,
    data: Any = None
) -> Dict[str, Any]:
    """Format success response"""
    from datetime import datetime
    return {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }