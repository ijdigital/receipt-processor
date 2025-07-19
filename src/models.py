"""
Pydantic models for API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
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


class SpecificationItem(BaseModel):
    """Model for individual specification item"""
    gtin: str = Field("", description="GTIN code")
    name: str = Field(..., description="Item name")
    quantity: float = Field(..., description="Item quantity")
    total: float = Field(..., description="Total amount")
    unit_price: float = Field(..., description="Unit price")
    label: str = Field("", description="Tax label")
    label_rate: float = Field(0, description="Tax rate")
    tax_base_amount: float = Field(0, description="Tax base amount")
    vat_amount: float = Field(0, description="VAT amount")


class SpecificationData(BaseModel):
    """Model for specification data"""
    success: bool = Field(True, description="Success status")
    items: List[SpecificationItem] = Field([], description="List of receipt items")


class ReceiptData(BaseModel):
    """Model for scraped receipt data"""
    status_racuna: Dict[str, Any] = Field(..., description="Receipt status section")
    zahtev_za_fiskalizaciju_racuna: Dict[str, Any] = Field(..., description="Fiscalization request section")
    rezultat_fiskalizacije_racuna: Dict[str, Any] = Field(..., description="Fiscalization result section")
    specifikacija_racuna: Optional[SpecificationData] = Field(None, description="Receipt specification section")


class ReceiptResponse(BaseModel):
    """Model for API response"""
    status: str = Field(..., description="Processing status")
    url: str = Field(..., description="Processed URL")
    processed_at: str = Field(..., description="Processing time")
    message: Optional[str] = Field(None, description="Additional message")
    data: Optional[ReceiptData] = Field(None, description="Scraped receipt data")


class ErrorResponse(BaseModel):
    """Model for errors"""
    detail: str = Field(..., description="Error description")