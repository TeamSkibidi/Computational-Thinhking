from typing import Dict

from fastapi import APIRouter, Depends

from app.application.services.event_service import EventService
from app.adapters.repositories.event_repository import MySQLEventRepository
 

from app.api.schemas.event.event_request import (
    EventSearchByNameRequest,
    EventListRequest,
    EventRecommendationRequest
)
from app.api.schemas.event.event_response import EventOut
from app.utils.response_format import success, error



router = APIRouter(prefix="/events", tags=["events"])


def get_event_service() -> EventService:
    repo = MySQLEventRepository()
    return EventService(repo)


@router.get("/search-by-name")
def search_events_by_name(
    params: EventSearchByNameRequest = Depends(),
    svc: EventService = Depends(get_event_service),
) -> Dict:
    """
    Tìm kiếm sự kiện / lễ hội theo tên.
    """
    try:
        events = svc.search_events_by_name(
            keyword=params.keyword,
            limit=params.limit,
        )
        data = [EventOut.from_entity(e) for e in events]
        return success("Tìm kiếm sự kiện thành công", data=data)
    except ValueError as e:
        return error(str(e))

@router.get("/list_event")
def list_events(
    params: EventListRequest = Depends(),
    svc: EventService = Depends(get_event_service),
) -> Dict:
    """
    Liệt kê danh sách sự kiện theo city, date, session, có thể sort.
    """
    try:
        events = svc.list_events(
            city=params.city,
            target_date=params.target_date,
            session=params.session,
            sort=params.sort,
        )
        data = [EventOut.from_entity(e) for e in events]
        return success("Lấy danh sách sự kiện thành công", data=data)
    except ValueError as e:
        return error(str(e))


@router.get("/recommendations")
def get_recommendations ( 
    params: EventRecommendationRequest = Depends(),
    svc: EventService = Depends(get_event_service),
) -> Dict :
    """
    Liệt kê danh sách sự kiện theo city, date, session, có thể sort.
    """
    try:
        events = svc.recommend_events (
                city = params.city,
                target_date = params.target_date,
                session = params.session,
                user_lng = params.lng,
                user_lat = params.lat
            )
        data = [EventOut.from_entity(e) for e in events]
        return success("Lấy danh sách sự kiện gợi ý thành công", data=data)
    except ValueError as e:
        return error(str(e))
    

@router.get("/detail/{event_id}")
def get_event(
    event_id: int,
    svc: EventService = Depends(get_event_service),
) -> Dict:
    """
    Lấy chi tiết một sự kiện cụ thể.
    """
    try:
        event = svc.get_event(event_id)
        if not event:
            return error("Event not found")
        data = EventOut.from_entity(event)
        return success("Lấy chi tiết sự kiện thành công", data=data)
    except ValueError as e:
        return error(str(e))
