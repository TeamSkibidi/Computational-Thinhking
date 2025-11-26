import json 
import asyncio
from datetime import datetime
from typing import List

from app.domain.entities.event import Event 
from app.adapters.repositories.mysql_event_repository import MySQLEventRepository
from app.scripts.seed_utils import load_events_from_json

JSON_PATH = "app/data/events.json"

async def main ():
    # 1. Load dữ liệu từ JSON
    events: List[Event] = load_events_from_json(JSON_PATH)
    print(f"Đọc được {len(events)} events từ {JSON_PATH}")

    if not events:
        print("Không có event nào để seed, dừng.")
        return 
    
    # 2. Tạo repo và upsert vào DB
    repo = MySQLEventRepository()
    await repo.upsert_events(events)
    print("✅ Đã seed xong events vào DB.")

if __name__== "__main__":
        asyncio.run(main())

