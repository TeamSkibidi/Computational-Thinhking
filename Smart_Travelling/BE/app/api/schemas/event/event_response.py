from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.domain.entities.event import Event
from app.utils.format_money import format_money

class EventOut(BaseModel):
    id: Optional[int]
    name: str
    city: str
    region: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    start_datetime: Optional[datetime]
    end_datetime: Optional[datetime]
    session: Optional[str]
    summary: Optional[str]
    activities: List[str]
    image_url: Optional[str]
    price_vnd: Optional[str]
    popularity: Optional[float]
    distance_km: Optional[float] = None

    @classmethod
    def from_entity(cls, e: Event) -> "EventOut":
        data = e.__dict__.copy()
        if e.price_vnd is not None:
            data["price_vnd"] = format_money(e.price_vnd)
        else:
            data["price_vnd"] = None        # nếu service có set thêm thuộc tính distance_km thì map sang luôn
        if "distance_km" not in data and hasattr(e, "distance_km"):
            data["distance_km"] = getattr(e, "distance_km")
        return cls(**data)



class EventListResponse(BaseModel):
    success: bool
    message: str
    data: List[EventOut]



class EventDetailResponse(BaseModel):
    success: bool
    message: str
    data: EventOut
