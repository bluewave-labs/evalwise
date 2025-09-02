import logging
import sys
from typing import Optional
import json
import traceback
from datetime import datetime
from config import settings

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, cls=CustomJSONEncoder)

def setup_logging():
    """Setup application logging configuration"""
    
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create formatter
    if settings.environment == 'development':
        # Use simple format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # Use JSON format for production
        formatter = JSONFormatter()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.root.addHandler(console_handler)
    logging.root.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Set specific logger levels
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name)

# Context manager for request logging
class RequestContext:
    """Context manager for request-specific logging"""
    
    def __init__(self, request_id: str, operation: str, user_id: Optional[str] = None):
        self.request_id = request_id
        self.operation = operation
        self.user_id = user_id
        self.start_time = datetime.utcnow()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        logger = get_logger('request')
        
        if exc_type:
            logger.error(
                f"Request failed: {self.operation}",
                extra={
                    'request_id': self.request_id,
                    'user_id': self.user_id,
                    'operation': self.operation,
                    'duration': duration,
                    'error': str(exc_val)
                }
            )
        else:
            logger.info(
                f"Request completed: {self.operation}",
                extra={
                    'request_id': self.request_id,
                    'user_id': self.user_id,
                    'operation': self.operation,
                    'duration': duration
                }
            )

# Initialize logging
setup_logging()