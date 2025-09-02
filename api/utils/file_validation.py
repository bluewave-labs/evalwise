"""
File upload validation utilities for security
"""
import io
import csv
import json
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
import pandas as pd
# import magic  # Optional - commented out for compatibility
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    """Comprehensive file upload validation"""
    
    # Allowed file types and their MIME types
    ALLOWED_EXTENSIONS = {'.csv', '.jsonl'}
    ALLOWED_MIME_TYPES = {
        'text/csv',
        'text/plain',
        'application/octet-stream'  # Sometimes CSV files are detected as this
    }
    
    # Security limits
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ROWS = 10000  # Maximum number of rows
    MAX_COLUMNS = 100  # Maximum number of columns
    MAX_CELL_SIZE = 1000  # Maximum characters per cell
    
    @classmethod
    async def validate_upload_file(
        cls, 
        file: UploadFile,
        allowed_extensions: Optional[List[str]] = None
    ) -> bytes:
        """
        Comprehensive validation of uploaded files
        Returns file content as bytes if valid
        """
        # Use default extensions if none provided
        if allowed_extensions is None:
            allowed_extensions = list(cls.ALLOWED_EXTENSIONS)
        
        # 1. Check file exists and has content
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # 2. Check file extension
        file_ext = None
        if '.' in file.filename:
            file_ext = '.' + file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # 3. Read file content with size limit
        try:
            content = await file.read()
        except Exception as e:
            logger.error(f"Error reading uploaded file: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error reading uploaded file"
            )
        
        # 4. Check file size
        if len(content) > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {cls.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file not allowed"
            )
        
        # 5. Validate MIME type using python-magic (disabled for compatibility)
        # try:
        #     mime_type = magic.from_buffer(content, mime=True)
        #     if mime_type not in cls.ALLOWED_MIME_TYPES:
        #         logger.warning(f"Suspicious file type detected: {mime_type} for file {file.filename}")
        #         # Don't reject immediately as CSV detection can be unreliable
        # except Exception as e:
        #     logger.warning(f"Could not detect MIME type: {e}")
        logger.info(f"Skipping MIME type validation for file {file.filename}")
        
        # 6. Content validation based on file type
        if file_ext == '.csv':
            cls._validate_csv_content(content)
        elif file_ext == '.jsonl':
            cls._validate_jsonl_content(content)
        
        return content
    
    @classmethod
    def _validate_csv_content(cls, content: bytes) -> None:
        """Validate CSV file content"""
        try:
            # Try to parse as CSV
            content_str = content.decode('utf-8')
            
            # Check for potential security issues
            cls._check_for_malicious_content(content_str)
            
            # Parse CSV and validate structure
            csv_reader = csv.reader(io.StringIO(content_str))
            rows = list(csv_reader)
            
            if len(rows) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CSV file is empty"
                )
            
            # Check row and column limits
            if len(rows) > cls.MAX_ROWS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Too many rows. Maximum: {cls.MAX_ROWS}"
                )
            
            # Check column count and cell size
            for row_idx, row in enumerate(rows):
                if len(row) > cls.MAX_COLUMNS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Too many columns in row {row_idx + 1}. Maximum: {cls.MAX_COLUMNS}"
                    )
                
                for cell in row:
                    if len(str(cell)) > cls.MAX_CELL_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Cell content too large in row {row_idx + 1}. Maximum: {cls.MAX_CELL_SIZE} characters"
                        )
            
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be valid UTF-8 encoded text"
            )
        except csv.Error as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CSV format: {str(e)}"
            )
    
    @classmethod
    def _validate_jsonl_content(cls, content: bytes) -> None:
        """Validate JSONL file content"""
        try:
            content_str = content.decode('utf-8')
            
            # Check for potential security issues
            cls._check_for_malicious_content(content_str)
            
            lines = content_str.strip().split('\n')
            
            if len(lines) > cls.MAX_ROWS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Too many lines. Maximum: {cls.MAX_ROWS}"
                )
            
            # Validate each line as JSON
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    continue
                
                try:
                    parsed = json.loads(line)
                    
                    # Check if it's a dict and validate size
                    if isinstance(parsed, dict):
                        if len(parsed) > cls.MAX_COLUMNS:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Too many fields in line {line_idx + 1}. Maximum: {cls.MAX_COLUMNS}"
                            )
                        
                        # Check field content size
                        for key, value in parsed.items():
                            if len(str(value)) > cls.MAX_CELL_SIZE:
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Field '{key}' too large in line {line_idx + 1}. Maximum: {cls.MAX_CELL_SIZE} characters"
                                )
                
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid JSON in line {line_idx + 1}: {str(e)}"
                    )
                    
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be valid UTF-8 encoded text"
            )
    
    @classmethod
    def _check_for_malicious_content(cls, content: str) -> None:
        """Check for potentially malicious content patterns"""
        
        # Check for script injection patterns
        suspicious_patterns = [
            '<script',
            'javascript:',
            'vbscript:',
            'onload=',
            'onerror=',
            'eval(',
            'exec(',
            '__import__',
            'subprocess',
            'os.system',
            'shell=True'
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                logger.warning(f"Suspicious content pattern detected: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File contains potentially malicious content"
                )