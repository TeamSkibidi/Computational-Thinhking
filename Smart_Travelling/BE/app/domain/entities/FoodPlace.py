from typing import Optional, List
from pydantic import BaseModel, Field
from .Address import Address

class FoodPlace(BaseModel):
    id: Optional[int] = Field(None, description="ID duy nhất của địa điểm")
    name: str = Field(..., description="Tên quán ăn / nhà hàng / cafe")
    category: str = Field(default="eat",description="Loại: eat / hotel / visit / other")
    summary: Optional[str] = Field(None,description="Mô tả ngắn về địa điểm")
    cuisine: Optional[str] = Field(None,description="Loại ẩm thực: Viet, Japanese, Korean...")
    priceVNDPerPerson: Optional[float] = Field(None,ge=0,description="Giá ước lượng một người/bữa (VND)")
    rating: Optional[float] = Field(None,ge=0,le=5,description="Rating từ 0–5")
    reviewCount: Optional[int] = Field(None,ge=0,description="Số lượng review")
    popularity: Optional[int] = Field(None,ge=0,description="Điểm phổ biến")
    openTime: Optional[str] = Field(None,pattern=r"^\d{2}:\d{2}$",example="08:00",description="Giờ mở cửa dạng HH:MM")
    closeTime: Optional[str] = Field(None,pattern=r"^\d{2}:\d{2}$",example="22:00",description="Giờ đóng cửa dạng HH:MM")
    phone: Optional[str] = Field(None,description="Số điện thoại liên hệ")
    tags: List[str] = Field(default_factory=list,description="Danh sách tag liên quan đến địa điểm")
    address: Optional[Address] = None

    def save(self) -> dict:
        """Convert ra dict để lưu DB / trả API thô"""
        return {
            "name": self.name,
            "category": self.category,
            "summary": self.summary,
            "cuisine": self.cuisine,
            "priceVNDPerPerson": self.priceVNDPerPerson,
            "rating": self.rating,
            "reviewCount": self.reviewCount,
            "popularity": self.popularity,
            "openTime": self.openTime,
            "closeTime": self.closeTime,
            "phone": self.phone,
            "tags": self.tags,
            "address": self.address.model_dump() if self.address else None,
        }

    @classmethod
    def from_json(cls, data: dict) -> "FoodPlace":
        return cls(**data)

