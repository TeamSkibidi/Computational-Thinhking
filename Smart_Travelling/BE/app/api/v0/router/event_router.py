
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.services.event_service import EventService
from app.adapters.repositories.event_repository import MySQLEventRepository
from app.api.schemas.event import EventOut  


router = APIRouter(prefix="/events", tags=["events"])


def get_event_service() -> EventService:
    repo = MySQLEventRepository()
    return EventService(repo)


@router.get("/recommendations", response_model=List[EventOut])
def get_recommendations(
    city: str,
    target_date: date,
    session: Optional[str] = None,
    price: Optional[int] = None,
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    max_distance_km: Optional[float] = Query(None, gt=0),
    svc: EventService = Depends(get_event_service),
):
    events = svc.recommend_events(
        city=city,
        target_date=target_date,
        session=session,
        price=price,
        user_lat=lat,
        user_lng=lng,
        max_distance_km=max_distance_km,
    )
    return [EventOut.from_entity(e) for e in events]


@router.get("/search-by-name", response_model=List[EventOut])
def search_events_by_name(
    keyword: str = Query(..., min_length=1, description="Tên lễ hội cần tìm"),
    limit: int = Query(5, ge=1, le=20),
    svc: EventService = Depends(get_event_service),
):

    events = svc.search_events_by_name(keyword=keyword, limit=limit)
    return [EventOut.from_entity(e) for e in events]


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: int,
    svc: EventService = Depends(get_event_service),
):
    event = svc.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventOut.from_entity(event)



@router.get("/", response_model=List[EventOut])
def list_events(
    city: str,
    target_date: date,
    session: Optional[str] = None,
    sort: Optional[str] = Query(
        None,
        description="price_asc | price_desc | popularity_desc",
    ),
    svc: EventService = Depends(get_event_service),
):
    events = svc.list_events(city, target_date, session, sort)
    return [EventOut.from_entity(e) for e in events]
