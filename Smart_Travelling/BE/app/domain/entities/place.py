from typing import Optional, List
from pydantic import BaseModel, Field
from .Address import Address

class Place(BaseModel):
    id: Optional[int] = Field(None, description="ID duy nhất")
    name: str = Field(..., description="Tên địa điểm")
    priceVND: Optional[float] = Field(None, ge=0, description="Giá tham khảo")
    summary: Optional[str] = Field (None, max_length = 160)
    description: Optional[str] = None
    openTime: Optional[str] = Field(None, pattern = r"^(([01]\d|2[0-3]):[0-5]\d)?$", example = "06:00")
    closeTime: Optional[str] = Field(None, pattern= r"^(([01]\d|2[0-3]):[0-5]\d)?$", example= "23:00")
    phone: Optional[str] = None
    rating: Optional[float] = Field(None, ge = 0, le = 5, example=4.5) 
    reviewCount: Optional[int] = Field(0, ge = 0, example = 12102006)
    popularity: Optional[int] = Field(None, ge = 0, le = 100, example= 87)
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    address: Optional[Address] = None
    

    # Hàm chuyển đổi chung
    def to_dict(self) -> dict:
        return self.model_dump()