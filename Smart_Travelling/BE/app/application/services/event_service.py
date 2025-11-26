from datetime import date
from typing import List, Optional

from app.domain.entities.event import Event
from app.application.interfaces.EventRepository import EventRepository

class EventService:
    def __init__ (self, repo: EventRepository):
        self.repo = repo
    
    async def list_events(self, city: str, target_date: date, session: Optional[str]) -> List[Event]:
        return await self.repo.get_events_for_city_date(city, target_date, session)
    
    async def recommend_events (self, city: str, target_date: date, session: Optional[str], price: Optional[int]) -> List[Event]:
        events = await self.repo.get_events_for_city_date (city, target_date, session)
        
        #sort theo gia tien( neu co) va độ phổ biến
        if price is not None:
            events = [
                e for e in events
                if e.price_vnd is None or e.price_vnd <= price
            ]

        events.sort(key=lambda e:(e.popularity or 0, e.price_vnd if e.price_vnd is not None else 0,), reverse=True,)

        return events
    
    