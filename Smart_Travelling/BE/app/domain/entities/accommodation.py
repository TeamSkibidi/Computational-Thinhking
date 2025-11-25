from typing import Optional, List, Any
from dataclasses import dataclass 
from pydantic import BaseModel, Field, field_validator
from .Address import Address

class Accommodation (BaseModel):
    name : Optional[str] = Field(..., description="Tên chỗ ở")
    capacity : Optional[int] = Field( None, ge = 1, description="Sức chứa tối đa")
    priceVND : Optional[float] = Field(None, ge=0, description="Giá ước lượng (VND)")       
    summary : Optional[str] = None 
    phone : Optional[str] = None
    rating : Optional[float] = Field (None, ge = 0, le = 5, description="Rating from 0 to 5")
    reviewCount: Optional[int] = Field (None, ge=0, description="Number of reviews")
    popularity : Optional[int] = Field(None, ge = 0, description ="Popularity score")
    category: Optional[str] = "Hotel"
    tags: List[str] = Field(default_factory=list,description="Danh sách tag liên quan đến địa điểm")
    address: Optional[Address] = None

    def save(self) -> dict:
        return {
        "name": self.name,
        "capacity": self.capacity,
        "priceVND": self.priceVND,
        "summary": self.summary,
        "phone": self.phone,
        "rating": self.rating,
        "reviewCount": self.reviewCount,
        "popularity": self.popularity,
        "category": self.category,
        "tags": self.tags,
        "address": self.address.model_dump() if self.address else None,
    }


    @classmethod
    def from_json(cls, data : dict) -> "Accommodation":
        return cls(**data)


