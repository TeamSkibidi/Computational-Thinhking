import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict
from app.config.setting import BASE_DIR


TRIP_HISTORY_DIR = os.path.join(BASE_DIR, "data", "trip_history")


def ensure_user_history_dir(user_id: int) -> Path:
    """Tạo folder lưu lịch sử nếu chưa tồn tại."""
    user_dir = Path(TRIP_HISTORY_DIR) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def save_trip_to_file(user_id: int, trip_data: Dict) -> bool:
    """Lưu 1 trip vào file JSON với tên là timestamp."""
    try:
        user_dir = ensure_user_history_dir(user_id)
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        trip_file = user_dir / f"trip_{timestamp}.json"
        
        trip_with_meta = {
            **trip_data,
            "id": timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with open(trip_file, "w", encoding="utf-8") as f:
            json.dump(trip_with_meta, f, ensure_ascii=False, indent=2, default=str,)
        
        print(f"✅ Saved trip for user {user_id} to {trip_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving trip: {e}")
        return False


def load_trip_history(user_id: int) -> List[Dict]:
    """Lấy toàn bộ lịch sử trip của user từ thư mục (mới nhất trước)."""
    try:
        user_dir = ensure_user_history_dir(user_id)
        trip_files = sorted(user_dir.glob("trip_*.json"), reverse=True)
        
        trips = []
        for trip_file in trip_files:
            try:
                with open(trip_file, "r", encoding="utf-8") as f:
                    trip = json.load(f)
                    trips.append(trip)
            except json.JSONDecodeError:
                print(f"⚠️ Invalid JSON: {trip_file}")
                continue
        
        return trips
    except Exception as e:
        print(f"❌ Error loading trip history: {e}")
        return []


def get_trip_detail(user_id: int, trip_id: int) -> Optional[Dict]:
    """Lấy chi tiết 1 trip theo trip_id (timestamp)."""
    try:
        user_dir = ensure_user_history_dir(user_id)
        trip_file = user_dir / f"trip_{trip_id}.json"
        
        if not trip_file.exists():
            return None
        
        with open(trip_file, "r", encoding="utf-8") as f:
            trip = json.load(f)
        
        return trip
    except Exception as e:
        print(f"❌ Error getting trip detail: {e}")
        return None


def delete_trip(user_id: int, trip_id: int) -> bool:
    """Xóa 1 trip file."""
    try:
        user_dir = ensure_user_history_dir(user_id)
        trip_file = user_dir / f"trip_{trip_id}.json"
        
        if trip_file.exists():
            trip_file.unlink()
            print(f"✅ Deleted trip {trip_id} for user {user_id}")
            return True
        
        return False
    except Exception as e:
        print(f"❌ Error deleting trip: {e}")
        return False


def delete_all_trips(user_id: int) -> bool:
    """Xóa toàn bộ lịch sử trip của user."""
    try:
        user_dir = ensure_user_history_dir(user_id)
        
        for trip_file in user_dir.glob("trip_*.json"):
            trip_file.unlink()
        
        print(f"✅ Deleted all trips for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting all trips: {e}")
        return False


def update_trip_access_time(user_id: int, trip_id: int) -> bool:
    """Cập nhật trip: xóa cũ, tạo mới với timestamp hiện tại (move lên top)."""
    try:
        old_trip = get_trip_detail(user_id, trip_id)
        if not old_trip:
            return False
        
        delete_trip(user_id, trip_id)
        return save_trip_to_file(user_id, old_trip)
    except Exception as e:
        print(f"❌ Error updating trip access time: {e}")
        return False