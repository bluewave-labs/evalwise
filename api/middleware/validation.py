"""
API request/response validation middleware
"""
import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from pydantic import BaseModel, ValidationError
import re

logger = logging.getLogger(__name__)

class APIValidationMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive API request/response validation and security middleware
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Request size limits
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_json_depth = 10
        self.max_query_params = 50
        self.max_header_size = 8192
        
        # Content validation patterns
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]
        
        # Compile regex patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
        
    async def dispatch(self, request: Request, call_next):
        # Skip validation for health check, static content, and auth endpoints
        skip_paths = ["/health", "/docs", "/openapi.json"]
        if request.url.path in skip_paths or request.url.path.startswith("/auth/"):
            return await call_next(request)
        
        try:
            # Validate request
            await self._validate_request(request)
            
            # Process request
            response = await call_next(request)
            
            # Validate response
            await self._validate_response(response, request)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Validation middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request validation failed"
            )
    
    async def _validate_request(self, request: Request) -> None:
        """Validate incoming request"""
        
        # 1. Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Maximum size: {self.max_request_size // (1024*1024)}MB"
            )
        
        # 2. Validate headers
        await self._validate_headers(request)
        
        # 3. Validate query parameters
        await self._validate_query_params(request)
        
        # 4. Validate request body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_request_body(request)
    
    async def _validate_headers(self, request: Request) -> None:
        """Validate request headers"""
        
        # Check header count and size
        if len(request.headers) > 100:  # Reasonable limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many headers"
            )
        
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > self.max_header_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Headers too large"
            )
        
        # Validate specific headers
        content_type = request.headers.get("content-type", "")
        if request.method in ["POST", "PUT", "PATCH"]:
            allowed_content_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
                "text/csv",
                "text/plain"
            ]
            
            if not any(ct in content_type.lower() for ct in allowed_content_types):
                logger.warning(f"Suspicious content type: {content_type}")
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported media type"
                )
        
        # Check for suspicious header values
        for name, value in request.headers.items():
            if self._contains_suspicious_content(value):
                logger.warning(f"Suspicious content in header {name}: {value[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid header content"
                )
    
    async def _validate_query_params(self, request: Request) -> None:
        """Validate query parameters"""
        
        query_params = dict(request.query_params)
        
        # Check parameter count
        if len(query_params) > self.max_query_params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many query parameters. Maximum: {self.max_query_params}"
            )
        
        # Validate parameter values
        for key, value in query_params.items():
            # Check parameter length
            if len(str(value)) > 1000:  # Reasonable limit
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Query parameter '{key}' too long"
                )
            
            # Check for suspicious content
            if self._contains_suspicious_content(str(value)):
                logger.warning(f"Suspicious content in query param {key}: {value}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid query parameter content"
                )
    
    async def _validate_request_body(self, request: Request) -> None:
        """Validate request body"""
        
        content_type = request.headers.get("content-type", "")
        
        # For JSON content
        if "application/json" in content_type:
            try:
                body = await request.body()
                if body:
                    # Check if it's valid JSON
                    json_data = json.loads(body.decode('utf-8'))
                    
                    # Validate JSON structure
                    self._validate_json_structure(json_data)
                    
                    # Check for suspicious content in JSON values
                    self._validate_json_content(json_data)
                    
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format"
                )
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid character encoding"
                )
    
    def _validate_json_structure(self, data: Any, depth: int = 0) -> None:
        """Validate JSON structure recursively"""
        
        if depth > self.max_json_depth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON structure too deep"
            )
        
        if isinstance(data, dict):
            if len(data) > 100:  # Reasonable limit for object properties
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON object has too many properties"
                )
            
            for key, value in data.items():
                if len(str(key)) > 100:  # Reasonable key length
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="JSON property name too long"
                    )
                self._validate_json_structure(value, depth + 1)
        
        elif isinstance(data, list):
            if len(data) > 1000:  # Reasonable limit for arrays
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON array too large"
                )
            
            for item in data:
                self._validate_json_structure(item, depth + 1)
        
        elif isinstance(data, str):
            if len(data) > 10000:  # Reasonable limit for strings
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON string value too long"
                )
    
    def _validate_json_content(self, data: Any) -> None:
        """Validate JSON content for suspicious patterns"""
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str) and self._contains_suspicious_content(key):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid content in JSON property name"
                    )
                self._validate_json_content(value)
        
        elif isinstance(data, list):
            for item in data:
                self._validate_json_content(item)
        
        elif isinstance(data, str):
            if self._contains_suspicious_content(data):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid content in JSON value"
                )
    
    def _contains_suspicious_content(self, content: str) -> bool:
        """Check if content contains suspicious patterns"""
        
        if not isinstance(content, str):
            return False
        
        # Check against compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return True
        
        return False
    
    async def _validate_response(self, response: StarletteResponse, request: Request) -> None:
        """Validate outgoing response"""
        
        # Add security headers if not present
        if "X-Content-Type-Options" not in response.headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Validate response size for data endpoints
        if hasattr(response, 'body'):
            content_length = len(response.body) if response.body else 0
            
            # Log large responses
            if content_length > 1024 * 1024:  # 1MB
                logger.info(
                    f"Large response: {content_length} bytes for {request.url.path}",
                    extra={'path': request.url.path, 'size': content_length}
                )
        
        # Ensure proper content type for JSON responses
        if hasattr(response, 'media_type'):
            if response.media_type == "application/json":
                response.headers.setdefault("Content-Type", "application/json; charset=utf-8")


class RequestSizeValidator:
    """Standalone request size validator for specific endpoints"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
    
    async def __call__(self, request: Request) -> Request:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Maximum size: {self.max_size // (1024*1024)}MB"
            )
        return request


# Pre-configured validators for common use cases
file_upload_validator = RequestSizeValidator(10 * 1024 * 1024)  # 10MB
json_api_validator = RequestSizeValidator(1024 * 1024)  # 1MB