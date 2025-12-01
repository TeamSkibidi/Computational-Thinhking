import json
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from app.domain.entities.event import Event
from app.application.interfaces.EventRepository import EventRepository
from app.infrastructure.database.connectdb import get_db

# 👇 THÊM IMPORT NÀY (sửa lại path cho đúng file của bạn nếu khác)
from app.utils.normalize_text import normalize_text


def _parse_activities(raw_value: Optional[str]) -> List[str]:
    """
    Chuyển cột activities (JSON string) trong DB về List[str].
    Nếu lỗi hoặc rỗng thì trả về [].
    """
    if not raw_value:
        return []
    try:
        data = json.loads(raw_value)
        # đảm bảo luôn là list
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _row_to_event(row: Dict[str, Any]) -> Event:
    """
    Helper chuyển 1 dòng dữ liệu (dict) từ DB về object Event.
    """
    return Event(
        id=row["id"],
        external_id=row["external_id"],
        name=row["name"],
        city=row["city"],
        region=row["region"],
        lat=float(row["lat"]) if row["lat"] is not None else None,
        lng=float(row["lng"]) if row["lng"] is not None else None,
        start_datetime=row["start_datetime"],
        end_datetime=row["end_datetime"],
        session=row["session"],
        summary=row["summary"],
        activities=_parse_activities(row.get("activities")),
        image_url=row["image_url"],
        price_vnd=row["price_vnd"],
        popularity=row["popularity"],
        source=row["source"],
    )


class MySQLEventRepository(EventRepository):
    def upsert_events(self, events: List[Event]) -> None:
        """
        Upsert danh sách events (sync, không async/aiomysql).
        - INSERT nếu external_id chưa tồn tại.
        - UPDATE nếu external_id đã tồn tại (dựa trên UNIQUE KEY/PRIMARY KEY ở DB).
        """
        if not events:
            return

        db = get_db()
        if db is None:
            return

        cursor = db.cursor()

        sql = """
        INSERT INTO events (
            external_id, name, city, region,
            lat, lng,
            start_datetime, end_datetime, session,
            summary, activities, image_url, price_vnd, popularity,
            source
        )
        VALUES (
            %(external_id)s, %(name)s, %(city)s, %(region)s,
            %(lat)s, %(lng)s,
            %(start_datetime)s, %(end_datetime)s, %(session)s,
            %(summary)s, CAST(%(activities)s AS JSON), %(image_url)s, %(price_vnd)s, %(popularity)s,
            %(source)s
        )
        ON DUPLICATE KEY UPDATE
            name           = VALUES(name),
            city           = VALUES(city),
            region         = VALUES(region),
            lat            = VALUES(lat),
            lng            = VALUES(lng),
            start_datetime = VALUES(start_datetime),
            end_datetime   = VALUES(end_datetime),
            session        = VALUES(session),
            summary        = VALUES(summary),
            activities     = VALUES(activities),
            image_url      = VALUES(image_url),
            price_vnd      = VALUES(price_vnd),
            popularity     = VALUES(popularity),
            updated_at     = CURRENT_TIMESTAMP;
        """

        params: List[Dict[str, Any]] = []
        for e in events:
            params.append(
                {
                    "external_id": e.external_id,
                    "name": e.name,
                    "city": e.city,
                    "region": e.region,
                    "lat": e.lat,
                    "lng": e.lng,
                    "start_datetime": e.start_datetime,
                    "end_datetime": e.end_datetime,
                    "session": e.session,
                    "summary": e.summary,
                    "activities": json.dumps(e.activities or []),
                    "image_url": e.image_url,
                    "price_vnd": e.price_vnd,
                    "popularity": e.popularity,
                    "source": e.source,
                }
            )

        cursor.executemany(sql, params)
        db.commit()

        cursor.close()
        db.close()

    def get_events_for_city_date(
        self,
        city: str,
        target_date: date,
        session: Optional[str] = None,
    ) -> List[Event]:
        """
        Lấy các events theo city + ngày (sync version).

        Điều kiện:
            start_datetime < end_of_day
            end_datetime   > start_of_day
        => event nào có giao với ngày target_date thì được tính.
        Nếu có session thì thêm filter (session = ? OR session IS NULL).

        LƯU Ý:
        - Để hỗ trợ gõ city có dấu / không dấu:
          + Không filter city trực tiếp trong SQL nữa.
          + Lọc theo city bằng Python với normalize_text().
        """
        db = get_db()
        if db is None:
            return []

        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        # BỎ ĐIỀU KIỆN city = %s TRONG SQL, chỉ lọc theo ngày + session
        sql = """
        SELECT
            id, external_id, name, city, region,
            lat, lng,
            start_datetime, end_datetime, session,
            summary, activities, image_url, price_vnd, popularity,
            source
        FROM events
        WHERE start_datetime < %s
          AND end_datetime > %s
        """
        params: List[Any] = [end_of_day, start_of_day]

        if session:
            sql += " AND (session = %s OR session IS NULL)"
            params.append(session)

        cursor = db.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        cursor.close()
        db.close()

        # Normalize city user nhập vào
        target_city_norm = normalize_text(city)

        events: List[Event] = []
        for row in rows:
            # Normalize city từ DB để so sánh
            db_city_norm = normalize_text(row["city"])
            if db_city_norm == target_city_norm:
                events.append(_row_to_event(row))

        return events

    def get_by_id(self, event_id: int) -> Optional[Event]:
        """
        Lấy chi tiết event theo id (sync version).
        """
        db = get_db()
        if db is None:
            return None

        sql = """
        SELECT
            id, external_id, name, city, region,
            lat, lng,
            start_datetime, end_datetime, session,
            summary, activities, image_url, price_vnd, popularity,
            source
        FROM events
        WHERE id = %s
        LIMIT 1
        """

        cursor = db.cursor(dictionary=True)
        cursor.execute(sql, (event_id,))
        row = cursor.fetchone()

        cursor.close()
        db.close()

        if not row:
            return None

        return _row_to_event(row)
    
    def search_events_by_name(self, keyword: str, limit: int = 5) -> List[Event]:
        """
        Tìm event theo tên / city / region, cho phép gõ không dấu.
        Đơn giản: load toàn bộ events, filter bằng normalize_text trong Python.
        Dataset của bạn nhỏ nên cách này ổn.
        """
        if not keyword:
            return []

        db = get_db()
        if db is None:
            return []

        cursor = db.cursor(dictionary=True)

        sql = """
        SELECT
            id, external_id, name, city, region,
            lat, lng,
            start_datetime, end_datetime, session,
            summary, activities, image_url, price_vnd, popularity,
            source
        FROM events
        """
        cursor.execute(sql)
        rows = cursor.fetchall()

        cursor.close()
        db.close()

        norm_kw = normalize_text(keyword)
        results: List[Event] = []

        for row in rows:
            e = _row_to_event(row)
            haystack = " ".join(
                [
                    normalize_text(e.name),
                    normalize_text(e.city or ""),
                    normalize_text(e.region or ""),
                ]
            )
            if norm_kw in haystack:
                results.append(e)
                if len(results) >= limit:
                    break

        return results

