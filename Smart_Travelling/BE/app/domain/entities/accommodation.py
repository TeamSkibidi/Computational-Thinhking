from typing import Optional
from pydantic import Field
from .place import Place

class Accommodation(Place):
    capacity: Optional[int] = Field(None, ge=1, description="Sức chứa tối đa")
    category: str = "Hotel" 
    summary: Optional[str] = None
    phone: Optional[str] = None

    def save(self) -> dict:
        data = self.model_dump()
        return data

    @classmethod
    def from_json(cls, data: dict) -> "Accommodation":
        return cls(**data)