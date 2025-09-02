from typing import Any, Dict, Optional, List
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class ErrorDetail(BaseModel):
    """Standard error detail structure"""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if validation error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class ErrorResponse(BaseModel):
    """Standard error response structure"""
    error: bool = Field(True, description="Always true for error responses")
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique error ID for tracking")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")
    message: str = Field(..., description="Main error message")
    details: List[ErrorDetail] = Field(default_factory=list, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID if available")

class APIException(HTTPException):
    """Base API exception with structured error responses"""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str,
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ):
        self.error_response = ErrorResponse(
            message=message,
            details=details or [],
            request_id=request_id
        )
        super().__init__(status_code=status_code, detail=self.error_response.dict())

# Specific exception classes
class ValidationError(APIException):
    """Validation error exception"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            request_id=request_id,
        )

class NotFoundError(APIException):
    """Resource not found exception"""
    
    def __init__(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
            
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=[ErrorDetail(
                code="RESOURCE_NOT_FOUND",
                message=message,
                details={"resource": resource, "resource_id": resource_id}
            )],
            request_id=request_id,
        )

class ConflictError(APIException):
    """Resource conflict exception"""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="RESOURCE_CONFLICT",
            details=details,
            request_id=request_id,
        )

class AuthenticationError(APIException):
    """Authentication failed exception"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTHENTICATION_FAILED",
            request_id=request_id,
        )

class AuthorizationError(APIException):
    """Authorization failed exception"""
    
    def __init__(
        self,
        message: str = "Access denied",
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="ACCESS_DENIED",
            request_id=request_id,
        )

class RateLimitError(APIException):
    """Rate limit exceeded exception"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None,
    ):
        details = []
        if retry_after:
            details.append(ErrorDetail(
                code="RETRY_AFTER",
                message=f"Retry after {retry_after} seconds",
                details={"retry_after": retry_after}
            ))
            
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            request_id=request_id,
        )

class InternalServerError(APIException):
    """Internal server error exception"""
    
    def __init__(
        self,
        message: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code=error_code,
            request_id=request_id,
        )