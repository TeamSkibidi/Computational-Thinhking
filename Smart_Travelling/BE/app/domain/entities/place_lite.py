from dataclasses import dataclass
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import time
from .place import Place
class PlaceLite(Place):
    category: Optional[str] = "visit"
    dwell: Optional[int] = Field(None, ge=0, example=90, description="Thời gian tham quan gợi ý tính bằng phút")

    def save(self) -> dict:
        data = self.model_dump()
        return data

    @classmethod
    def from_json(cls, data: dict) -> "PlaceLite":
        return cls(**data)
        
