from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, List

@dataclass
class Event:
    id : Optional[int]
    external_id: str
    name: str
    city: str
    region: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    start_datetime: Optional[datetime]
    end_datetime: Optional [datetime]
    session: Optional[str]      # "morning" | "afternoon" | "evening" | "full_day"
    summary: Optional[str]
    activities: List[str]
    image_url: Optional[str]
    price_vnd: Optional[str] # neu co gia ve vao cong 
    popularity: Optional[float]
    source: str                 # tên API/provider