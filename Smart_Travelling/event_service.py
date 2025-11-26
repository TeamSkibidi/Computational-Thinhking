from datetime import date
from typing import List, Optional
from math import radians, sin, cos, asin, sqrt

from app.domain.entities.event import Event
from app.application.interfaces.EventRepository import EventRepository


class EventService:
    def __init__(self, repo: EventRepository):
        self.repo = repo

    async def list_events(
        self,
        city: str,
        target_date: date,
        session: Optional[str],
    ) -> List[Event]:
        return await self.repo.get_events_for_city_date(city, target_date, session)

    async def recommend_events(
        self,
        city: str,
        target_date: date,
        session: Optional[str] = None,
        price: Optional[int] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        max_distance_km: Optional[float] = None,
    ) -> List[Event]:
        # Lấy events thô cho city + date + session
        events = await self.repo.get_events_for_city_date(city, target_date, session)

        # 1️⃣ Lọc theo price (nếu có)
        if price is not None:
            events = [
                e for e in events
                if e.price_vnd is None or e.price_vnd <= price
            ]


        # 3. Nếu có GPS → tính distance_km + sort theo khoảng cách
        if user_lat is not None and user_lng is not None:
            for e in events:
                if e.lat is not None and e.lng is not None:
                    e.distance_km = self._haversine_km(user_lat, user_lng, e.lat, e.lng)
                else:
                    # event không có toạ độ → không tính được
                    e.distance_km = None

            if max_distance_km is not None:
                events = [
                    e for e in events
                    if e.distance_km is not None and e.distance_km <= max_distance_km
                ]


        # 4. Sort theo độ phổ biến + giá (như bạn đã làm)
        events.sort(
            key=lambda e: (
                e.popularity or 0,
                e.price_vnd if e.price_vnd is not None else 0,
            ),
            reverse=True,
        )

        return events

    async def get_event(self, event_id: int) -> Event | None:
        return await self.repo.get_by_id(event_id)

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0  # km

        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)

        a = (
            sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
        )
        c = 2 * asin(sqrt(a))
        return R * c
