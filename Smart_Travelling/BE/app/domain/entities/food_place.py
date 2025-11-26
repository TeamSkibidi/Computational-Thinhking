from typing import Optional
from pydantic import Field
from .place import Place

class Food(Place):
    cuisine_type: Optional[str] = Field(None, description="Loại ẩm thực: Á, Âu, Chay...")
    category: str = "eat"
    phone: Optional[str] = None
    menu_url: Optional[str] = None
    
    def save(self) -> dict:
        data = self.model_dump()
        return data

    @classmethod
    def from_json(cls, data: dict) -> "Food":
        return cls(**data)