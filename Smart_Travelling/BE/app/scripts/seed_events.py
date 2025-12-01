from typing import List

from app.domain.entities.event import Event
from app.adapters.repositories.event_repository import MySQLEventRepository
from app.scripts.seed_utils import load_events_from_csv  # 👈 dùng CSV

CSV_PATH = "DB/event.csv"   # chỉnh lại path cho đúng

def main():
    events: List[Event] = load_events_from_csv(CSV_PATH)
    print(f"Đọc được {len(events)} events từ {CSV_PATH}")

    if not events:
        print("Không có event nào để seed, dừng.")
        return

    repo = MySQLEventRepository()
    repo.upsert_events(events)     # ❌ không dùng await nữa
    print("✅ Đã seed xong events vào DB.")

if __name__ == "__main__":
    main()
