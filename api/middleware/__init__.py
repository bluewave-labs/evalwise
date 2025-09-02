import uuid
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from utils.logging import get_logger, RequestContext
from utils.errors import ErrorResponse, InternalServerError
import traceback

logger = get_logger(__name__)

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track requests and add request IDs"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to headers
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'query': str(request.query_params),
                'client_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent')
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration': round(duration, 3)
                }
            )
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration': round(duration, 3),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            
            # Return structured error response
            error_response = ErrorResponse(
                message="Internal server error",
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.dict(),
                headers={'X-Request-ID': request_id}
            )

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle and format exceptions"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
            
            # Log the error
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                exc_info=e,
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path
                }
            )
            
            # Create error response
            error_response = ErrorResponse(
                message="Internal server error occurred",
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.dict(),
                headers={'X-Request-ID': request_id}
            )