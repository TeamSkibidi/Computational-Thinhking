from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.domain.entities.event import Event 

class EventRepository(ABC):
    @abstractmethod
    def upsert_events(self, events: List[Event]) -> None:
        """
        Lưu list Event vào DB (insert hoặc update nếu đã tồn tại).
        """
        pass

    @abstractmethod
    def get_events_for_city_date (
        self,
        city: str,
        target_date: date,
        session: Optional[str] = None
    ) -> List[Event]:
        """
        Lấy events trong 1 city, 1 ngày, có thể filter theo session.
        """
        pass
    
    @abstractmethod
    def get_by_id (self, event_id: int) -> Optional[Event]:
        pass