from dataclasses import dataclass
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import time
from .Address import Address
from .place import Place
class PlaceLite(Place):
    phone: Optional[str] = Field(None, example ="0375 256 105")
    category: Optional[str] = "visit"
    dwell: Optional[int] = Field(None, ge=0, example=90, description="Thời gian tham quan gợi ý tính bằng phút")
    imageName: Optional[str] = Field(None, example="Nha_tho_duc_ba.png")

    def save(self) -> dict:
        data = self.model_dump()
        return data

    @classmethod
    def from_json(cls, data: dict) -> "PlaceLite":
        return cls(**data)
        
