"""
Pydantic modeli za API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class ReceiptRequest(BaseModel):
    """Model za zahtev koji prima URL računa"""
    url: str = Field(..., description="URL skeniranog računa")
    
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL ne može biti prazan')
        
        # Osnovna URL validacija
        url_pattern = re.compile(
            r'^https?://'  # http:// ili https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domen
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...ili IP
            r'(?::\d+)?'  # opciono port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Nevaljan URL format')
        
        # Proveri da li je sa suf.purs.gov.rs domena
        if 'suf.purs.gov.rs' not in v:
            raise ValueError('URL mora biti sa suf.purs.gov.rs domena')
        
        return v


class ReceiptResponse(BaseModel):
    """Model za odgovor API-ja"""
    status: str = Field(..., description="Status obrade")
    url: str = Field(..., description="Obrađeni URL")
    processed_at: str = Field(..., description="Vreme obrade")
    message: Optional[str] = Field(None, description="Dodatna poruka")


class ErrorResponse(BaseModel):
    """Model za greške"""
    detail: str = Field(..., description="Opis greške")