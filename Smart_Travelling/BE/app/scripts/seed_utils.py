import json 
import re
from datetime import datetime 
from typing import List, Optional

from app.domain.entities.event import Event 
from app.utils.build_datetime import build_datetime

def load_events_from_json (path: str) -> List[Event]:
    with open (path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    events: List[Event] =[]
    for item in raw:
        date_str = item.get("date")
        start_dt = build_datetime(date_str, item.get("start_time"))
        end_dt = build_datetime(date_str, item.get("end_time"))
    
        events.append (
            Event(
                id=None,
                external_id=item["external_id"],
                name=item["name"],
                city=item["city"],
                region=item.get("region"),
                lat=item.get("lat"),
                lng=item.get("lng"),
                start_datetime=start_dt,
                end_datetime=end_dt,
                session=item.get("session"),
                summary=item.get("summary"),
                activities=item.get("activities") or [],
                image_url=item.get("image_url"),
                price_vnd=item.get("price_vnd"),
                popularity=item.get("popularity"),
                source=item.get("source", "manual_seed"),
            )
        )

    return events
