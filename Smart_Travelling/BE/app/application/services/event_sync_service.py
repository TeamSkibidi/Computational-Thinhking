from datetime import date
from typing import List
from abc import ABC
from app.domain.entities.event import Event
from app.application.interfaces.EventRepository import EventRepository
from app.infrastructure.client.event_api_client import EventAPIClient

class EventSyncService:
    
    def __init__ (self, repo: EventRepository, api_client: EventAPIClient):
        self.repo = repo
        self.api_client = api_client

    
    async def sync_city_date (self, city: str, target_date: date) -> List[Event]:
        events = self.api_client.fetch_events(city, target_date)
        await self.repo.upsert_events(events)
        return events