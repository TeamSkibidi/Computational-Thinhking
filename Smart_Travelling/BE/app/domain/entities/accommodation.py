from typing import Optional
from pydantic import Field
from .place import Place
from datetime import date

class Accommodation(Place):
    capacity: Optional[int] = Field(None, ge=1, description="Sức chứa tối đa")
    category: str = "Hotel" 
    phone: Optional[str] = None
    num_guest : Optional[int] =  Field (None, ge = 0, description = "So luong khach") 
    def save(self) -> dict:
        data = self.model_dump()
        return data

    @classmethod
    def from_json(cls, data: dict) -> "Accommodation":
        return cls(**data)