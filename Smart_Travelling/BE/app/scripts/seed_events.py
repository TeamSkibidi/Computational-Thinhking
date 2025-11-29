import asyncio
from typing import List

from app.domain.entities.event import Event
from Smart_Travelling.BE.app.adapters.repositories.event_repository import MySQLEventRepository
from app.scripts.seed_utils import load_events_from_csv  # 👈 dùng CSV

CSV_PATH = "DB.events.csv"


async def main():
    # 1. Load dữ liệu từ CSV
    events: List[Event] = load_events_from_csv(CSV_PATH)
    print(f"Đọc được {len(events)} events từ {CSV_PATH}")

    if not events:
        print("Không có event nào để seed, dừng.")
        return

    # 2. Tạo repo và upsert vào DB
    repo = MySQLEventRepository()
    await repo.upsert_events(events)
    print("✅ Đã seed xong events vào DB.")


if __name__ == "__main__":
    asyncio.run(main())
