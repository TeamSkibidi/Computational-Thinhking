from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
import re


class Address(BaseModel):
    houseNumber: Optional[str] = None
    street: Optional[str] = None
    ward: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude between -90 and 90")
    lng: Optional[float] = Field(None, ge=-180, le=180, description="Longitude between -180 and 180")
    url: Optional[str] = None

    def get_full_address(self) -> str:
        parts = [
            self.houseNumber,
            self.street,
            self.ward,
            self.district,
            self.city
        ]
        return ", ".join(filter(None, parts))


class Place(BaseModel):
    id: Optional[int] = None
    name: str
    priceVnd: Optional[int] = Field(None, ge=0, description="Price in VND, must be >= 0")
    summary: Optional[str] = None
    description: Optional[str] = None
    openTime: Optional[str] = Field(None, description="Opening time in HH:MM format")
    closeTime: Optional[str] = Field(None, description="Closing time in HH:MM format")
    phone: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating from 0 to 5")
    reviewCount: Optional[int] = Field(None, ge=0, description="Number of reviews")
    popularity: Optional[int] = Field(None, ge=0, description="Popularity score")
    imageName: Optional[str] = None
    address: Optional[Address] = None

    @field_validator('openTime', 'closeTime')
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
        if not time_pattern.match(v):
            raise ValueError(f'Time must be in HH:MM format (00:00 - 23:59), got: {v}')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Remove spaces and common separators
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{9,15}$', cleaned):
            raise ValueError(f'Invalid phone number format: {v}')
        return v

    def to_json(self) -> dict:
        return self.model_dump(exclude_none=False)

    @classmethod
    def from_json(cls, data: dict) -> "Place":
        return cls(**data)

    def format_money(self) -> Optional[str]:
        if self.priceVnd is None:
            return None
        return f"{self.priceVnd:,.0f} VNĐ".replace(",", ".")
    
    def is_open_now(self) -> Optional[bool]:
        if not self.openTime or not self.closeTime:
            return None
        
        from datetime import datetime
        now = datetime.now().time()
        
        try:
            open_h, open_m = map(int, self.openTime.split(':'))
            close_h, close_m = map(int, self.closeTime.split(':'))
            
            from datetime import time
            open_time = time(open_h, open_m)
            close_time = time(close_h, close_m)
            
            # Handle overnight hours (e.g., 22:00 - 02:00)
            if close_time < open_time:
                return now >= open_time or now <= close_time
            else:
                return open_time <= now <= close_time
        except:
            return None


class ApiResponse(BaseModel):
    success: bool = True
    message: str = ""
    query: Optional[str] = None
    page: int = Field(1, ge=1, description="Current page number, must be >= 1")
    pageTotal: int = Field(1, ge=1, description="Total number of pages")
    hasNextPage: bool = False
    hasPrevPage: bool = False
    count: int = Field(0, ge=0, description="Number of items in current page")
    data: List[Any] = Field(default_factory=list)

    def to_json(self) -> dict:
        return self.model_dump(exclude_none=False)
    
    @classmethod
    def success_response(cls, data: List[Any], query: str = "", page: int = 1, total_items: int = 0, page_size: int = 20) -> "ApiResponse":
        page_total = max(1, (total_items + page_size - 1) // page_size)
        return cls(
            success=True,
            message="OK",
            query=query,
            page=page,
            pageTotal=page_total,
            hasNextPage=page < page_total,
            hasPrevPage=page > 1,
            count=len(data),
            data=data
        )
    
    @classmethod
    def error_response(cls, message: str, query: str = "") -> "ApiResponse":
        return cls(
            success=False,
            message=message,
            query=query,
            data=[]
        )
