from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field
from datetime import time
from .Address import Address

class PlaceLite(BaseModel):
    id: Optional[int] = Field(None, example=123)
    name: str = Field(..., example="Nhà Thờ Đức Bà")
    priceVnd: Optional[int] = Field(None, ge=0, example=35000, description="Giá tham khảo")
    summary: Optional[str] = Field (None, max_length = 160)
    description: Optional[str] = None
    openTime: Optional[str] = Field(None, pattern = r"^(([01]\d|2[0-3]):[0-5]\d)?$", example = "06:00")
    closeTime: Optional[str] = Field(None, pattern= r"^(([01]\d|2[0-3]):[0-5]\d)?$", example= "23:00")
    phone: Optional[str] = Field(None, example ="0375 256 105")
    rating: Optional[float] = Field(None, ge = 0, le = 5, example=4.5) 
    reviewCount: Optional[int] = Field(0, ge = 0, example = 12102006)
    popularity: Optional[int] = Field(None, ge = 0, le = 100, example= 87)
    category: Optional[str] = None
    dwell: Optional[int] = Field(None, ge=0, example=90, description="Thời gian tham quan gợi ý tính bằng phút")
    imageName: Optional[str] = Field(None, example="Nha_tho_duc_ba.png")
    imageUrl: Optional[str] = Field(
        None,
        example="https://cdn.example.com/img/banhmi-huynhhoa.jpg"
    )
    tags: Optional[list[str]] = Field(default_factory=list, description="Danh sách tag liên quan đến địa điểm")
    address: Address


    def open_now(self) -> Optional[bool]:
        if self.openTime is None or self.closeTime is None:
            return None

        from datetime import datetime, time
        now = datetime.now().time()
        open_time = time.fromisoformat(self.openTime)
        close_time = time.fromisoformat(self.closeTime)

        if open_time < close_time:
            return open_time <= now <= close_time
        else:
            return now >= open_time or now <= close_time

        
