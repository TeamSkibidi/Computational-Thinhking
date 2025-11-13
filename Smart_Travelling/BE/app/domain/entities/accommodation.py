from typing import Optional, List, Any
from dataclasses import dataclass 
from pydantic import BaseModel, Field, field_validator
import re
from domain.entities.Address import Address
# class Address(BaseModel):
#     houseNumber: Optional[str] = None
#     street: Optional[str] = None
#     ward: Optional[str] = None
#     district: Optional[str] = None
#     city: Optional[str] = None
#     lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude between -90 and 90")
#     lng: Optional[float] = Field(None, ge=-180, le=180, description="Longitude between -180 and 180")
#     url: Optional[str] = None

# def get_full_address(self) -> str:
#     parts = [
#         self.houseNumber,
#         self.street,
#         self.ward,
#         self.district,
#         self.city
#     ]
#     return ", ".join(filter(None, parts))

class Accommodation (BaseModel):
    name : Optional[str]
    capacity : Optional[int] 
    priceVND : Optional[float]
    summary : Optional[str] = None
    phone : Optional[str] = None
    rating : Optional[float] = Field (None, ge = 0, le = 5, description="Rating from 0 to 5")
    reviewCount: Optional[int] = Field (None, ge=0, description="Number of reviews")
    popularity : Optional[int] = Field(None, ge = 0, description ="Popularity score")
    address: Optional[Address] = None

    def save (self) -> dict :
        return {
            "name" : self.name,
            "capacity" : self.capacity,
            "priceVND" : self.priceVND,
            "summary" : self.summary,
            "phone" : self.phone,
            "rating" : self.rating,
            "reviewCount" : self.reviewCount,
            "populariy" : self.popularity,
            "address" : self.address
        }

    @classmethod
    def from_json(cls, data : dict) -> "Accommodation":
        return cls(**data)



