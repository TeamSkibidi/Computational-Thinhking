from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query

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
    distance_km: Optional[float] = None

    @classmethod 
    def from_entity(cls, e: Event) -> "EventOut":
        data = e.__dict__.copy()
        data["price_vnd"] = format_money(e.price_vnd)
        if "distance_km" not in data and hasattr(e, "distance_km"):
            data["distance_km"] = getattr(e, "distance_km")
        return cls (**data)
    

  # goi y theo khoang cach, gia tien , do noi tieng  
@router.get("/recommendations", response_model=List[EventOut])
async def get_recommendations(city: str, target_date: date, 
                        session: Optional[str]=None, 
                        price: Optional[int]=None,
                        lat: Optional[float]=Query(None, ge=-90, le=90),
                        lng: Optional[float]=Query(None, ge=-180, le=180),
                        max_distance_km: Optional[float] = Query (None, gt=0, description= "Tu 5-7km"),
                        svc: EventService = Depends(get_event_service),
):
    events = await svc.recommend_events(
        city = city,
        target_date = target_date,
        session = session,
        price = price,
        user_lat=lat,
        user_lng=lng,
        max_distance_km = max_distance_km
    )

    result: List[EventOut] = []
    for e in events:
        item = EventOut.from_entity(e)
        result.append(item)
    return result

@router.get("/{event_id}", response_model=EventOut)
async def get_event( event_id: int, svc: EventService = Depends(get_event_service),):
    event = await svc.get_event(event_id)
    if not event: 
        raise HTTPException(status_code=404, detail="Event not found")
    return EventOut.from_entity(event)

# Liet ke toan bo nhung event 
@router.get("/", response_model=List[EventOut])
async def list_events(
    city: str,
    target_date: date,
    session: Optional[str] = None,
    svc: EventService = Depends(get_event_service),
):
    events = await svc.list_events(city, target_date, session)
    return [EventOut.from_entity(e) for e in events]
