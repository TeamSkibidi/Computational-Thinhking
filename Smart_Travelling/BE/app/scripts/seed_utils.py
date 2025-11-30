import csv
from typing import List, Optional

from app.domain.entities.event import Event
from app.utils.build_datetime import build_datetime


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)


def _split_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def load_events_from_csv(path: str) -> List[Event]:
    events: List[Event] = []

    with open(path, "r", encoding="utf-8", newline="") as f:
        raw = csv.DictReader(f)

        for item in raw:
            date_str = item.get("date")
            start_dt = build_datetime(date_str, item.get("start_time"))
            end_dt = build_datetime(date_str, item.get("end_time"))

            events.append(
                Event(
                    id=None,
                    external_id=item["external_id"],
                    name=item["name"],
                    city=item["city"],
                    region=(item.get("region") or None),
                    lat=_parse_float(item.get("lat")),
                    lng=_parse_float(item.get("lng")),
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    session=(item.get("session") or None),
                    summary=(item.get("summary") or None),
                    activities=_split_list(item.get("activities")),
                    image_url=(item.get("image_url") or None),
                    price_vnd=_parse_int(item.get("price_vnd")),
                    popularity=item.get(item.get("popularity")),
                    source=item.get("source","manual_seed"),
                )
            )

    return events
