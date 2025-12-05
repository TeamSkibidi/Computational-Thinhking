from datetime import date
from typing import List, Optional

from app.domain.entities.event import Event
from app.application.interfaces.EventRepository import EventRepository
from app.utils.geo_utils import haversine_km
from app.config.setting import MAX_LEG_DISTANCE_KM_DEFAULT


class EventService:
    def __init__(self, repo: EventRepository):
        self.repo = repo

    # ========================
    # 1) LIST EVENTS (sort đơn giản)
    # ========================
    def list_events(
        self,
        city: str,
        target_date: date,
        session: Optional[str],
        sort: Optional[str] = None,
    ) -> List[Event]:
        """
        Lấy danh sách event theo city + date (+ session).
        Nếu sort có giá trị, sort luôn ở BE:
          - price_asc     : giá tăng dần
          - price_desc    : giá giảm dần
          - popularity_desc: độ nổi tiếng giảm dần
        """
        events = self.repo.get_events_for_city_date(city, target_date, session)

        if not sort:
            return events

        if sort == "price_asc":
            events.sort(
                key=lambda e: e.price_vnd if e.price_vnd is not None else 10**12
            )
        elif sort == "price_desc":
            events.sort(
                key=lambda e: e.price_vnd if e.price_vnd is not None else -1,
                reverse=True,
            )
        elif sort == "popularity_desc":
            events.sort(
                key=lambda e: e.popularity if e.popularity is not None else -1,
                reverse=True,
            )

        return events

    # ========================
    # 2) RECOMMEND EVENTS (dùng cho sort theo khoảng cách)
    # ========================
    def recommend_events(
        self,
        city: str,
        target_date: date,
        session: Optional[str] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        max_distance_km: Optional[float] = None,
    ) -> List[Event]:
        """
        - Nếu có GPS:
            + luôn tính distance_km
            + nếu max_distance_km != None: lọc theo bán kính
            + sort theo: distance ↑
        """
        # 0) Lấy events thô
        events = self.repo.get_events_for_city_date(city, target_date, session)

        # 2) Có GPS -> tính khoảng cách + (tuỳ chọn) lọc theo max_distance_km
        if user_lat is not None and user_lng is not None:
            for e in events:
                if e.lat is not None and e.lng is not None:
                    e.distance_km = haversine_km(user_lat, user_lng, e.lat, e.lng)
                else:
                    e.distance_km = None

            if max_distance_km is not None:
                events = [
                    e for e in events
                    if e.distance_km is not None and e.distance_km <= max_distance_km
                ]

            # sort: gần → xa, trong cùng khoảng cách thì
            #   popularity cao hơn trước, rồi giá thấp hơn trước
        events.sort(
            key=lambda e: (
                e.distance_km if e.distance_km is not None else 1e9,
                -(e.popularity if e.popularity is not None else 0),
                e.price_vnd if e.price_vnd is not None else 10**12,
            )
        )

        return events

    # ========================
    # 3) GET DETAIL CỦA EVENT + SEARCH
    # ========================
    def get_event(self, event_id: int) -> Optional[Event]:
        return self.repo.get_by_id(event_id)

    def search_events_by_name(self, keyword: str, limit: int = 5) -> List[Event]:
        return self.repo.search_events_by_name(keyword=keyword, limit=limit)
