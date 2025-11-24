from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from app.application.services.event_service import EventService
from app.adapters.repositories.mysql_event_repository import MySQLEventRepository
from app.domain.entities.event import Event 
from app.utils.format_money import format_money

router = APIRouter(prefix="/events", tags=["events"])

def get_event_service() -> EventService:
    repo = MySQLEventRepository()
    return EventService(repo)

class EventOut(BaseModel):
    id: Optional[int]
    external_id: str
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

    @classmethod 
    def from_entity(cls, e: Event) -> "EventOut":
        data = e.__dict__.copy()
        data["price_vnd"] = format_money(e.price_vnd)
        return cls (**data)
    
@router.get("/recommendations", response_model=List[EventOut])
async def get_recommendations(city: str, target_date: date, session: Optional[str], 
                        price: Optional[int],
                         svc: EventService = Depends(get_event_service),
):
    events = await svc.recommend_events(city, target_date, session, price)

    result: List[EventOut] = []
    for e in events:
        item = EventOut.from_entity(e)
        result.append(item)
    return result

@router.get("/{event_id}", response_model=EventOut)
async def get_event( event_id: int, svc: EventService = Depends(get_event_service),):
    event = await svc.repo.get_by_id(event_id)
    if not event: 
        raise HTTPException(status_code=404, detail="Event not found")
    return EventOut.from_entity(event)