"""
Custom exceptions and error handling for LMS
"""
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """Standard error codes across API"""
    AUTH_FAILED = "AUTH_001"
    INVALID_TOKEN = "AUTH_002"
    UNAUTHORIZED = "AUTH_003"

    RESOURCE_NOT_FOUND = "RESOURCE_404"
    INVALID_INPUT = "INPUT_400"
    CONFLICT = "CONFLICT_409"

    UPLOAD_FAILED = "UPLOAD_500"
    AI_PROCESSING_FAILED = "AI_500"
    STORAGE_ERROR = "STORAGE_500"

    SERVER_ERROR = "SERVER_500"


class LMSException(Exception):
    """Base exception for LMS"""

    def __init__(
            self,
            message: str,
            code: ErrorCode,
            status_code: int = 500,
            details: Optional[dict] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthException(LMSException):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.AUTH_FAILED):
        super().__init__(message, code, status_code=401)


class NotFoundException(LMSException):
    def __init__(self, message: str, resource: str = "Resource"):
        super().__init__(
            f"{resource} not found: {message}",
            ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404
        )


class ValidationException(LMSException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message,
            ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details
        )


class StorageException(LMSException):
    def __init__(self, message: str):
        super().__init__(
            message,
            ErrorCode.STORAGE_ERROR,
            status_code=500
        )


class AIProcessingException(LMSException):
    def __init__(self, message: str):
        super().__init__(
            message,
            ErrorCode.AI_PROCESSING_FAILED,
            status_code=500
        )