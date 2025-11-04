from typing import Optional
from pydantic import BaseModel, Field

class Address(BaseModel):
    houseNumber: Optional[str] = Field(None, example="26 or 32/14")
    street: Optional[str] = Field(None, example = "Thiên phước")
    ward: Optional[str] = Field(None, example="Phường 9")
    district: Optional[str] = Field(None, example="Quận Tân Bình")
    city: Optional[str] = Field(None, example="Thành Phố Hồ Chí Minh")
    lat: Optional[float] = Field(None, ge=-90, le=90,example=12.102006)
    lng: Optional[float] = Field(None, ge=-180, le=180, example=10.122006)
    url: Optional[str] = Field(None, example="https://maps.google.com/?q=10.122006,106.102006")