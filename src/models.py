"""
Pydantic models for API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class ReceiptRequest(BaseModel):
    """Model for request that receives receipt URL"""
    url: str = Field(..., description="URL of scanned receipt")
    
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        
        # Check if it's from suf.purs.gov.rs domain
        if 'suf.purs.gov.rs' not in v:
            raise ValueError('URL must be from suf.purs.gov.rs domain')
        
        return v


class ReceiptResponse(BaseModel):
    """Model for API response"""
    status: str = Field(..., description="Processing status")
    url: str = Field(..., description="Processed URL")
    processed_at: str = Field(..., description="Processing time")
    message: Optional[str] = Field(None, description="Additional message")


class ErrorResponse(BaseModel):
    """Model for errors"""
    detail: str = Field(..., description="Error description")