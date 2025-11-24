import json
from datetime import date, datetime, timedelta
from typing import List, Optional

import aiomysql

from app.domain.entities.event import Event
from app.application.interfaces.EventRepository import EventRepository
from app.infrastructure.database.connection import get_connection


class MySQLEventRepository(EventRepository):
    async def upsert_events(self, events: List[Event]) -> None:
        # print("[DEBUG] Fake upsert, events =", len(events))
        # return
         if not events:
             return
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
             name = VALUES(name),
             city = VALUES(city),
             region = VALUES(region),
             lat = VALUES(lat),
             lng = VALUES(lng),
             start_datetime = VALUES(start_datetime),
             end_datetime = VALUES(end_datetime),
             session = VALUES(session),
             summary = VALUES(summary),
             activities = VALUES(activities),
             image_url = VALUES(image_url),
             price_vnd = VALUES(price_vnd),
             popularity = VALUES(popularity),
             updated_at = CURRENT_TIMESTAMP;
         """

         params = []
         for e in events:
             params.append({
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
             })
         async with get_connection() as conn:
             async with conn.cursor() as cur:
                 await cur.executemany(sql, params)

    async def get_events_for_city_date(
        self,
        city: str,
        target_date: date,
        session: Optional[str] = None,
    ) -> List[Event]:
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        sql = """
        SELECT
            id, external_id, name, city, region,
            lat, lng,
            start_datetime, end_datetime, session,
            summary, activities, image_url, price_vnd, popularity,
            source
        FROM events
        WHERE city = %s
          AND start_datetime < %s
          AND end_datetime > %s
        """
        params = [city, end_of_day, start_of_day]

        if session:
            sql += " AND (session = %s OR session IS NULL)"
            params.append(session)

        events: List[Event] = []

        async with get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()

        for row in rows:
            activities = []
            if row["activities"]:
                try:
                    activities = json.loads(row["activities"])
                except Exception:
                    activities = []

            events.append(Event(
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
                activities=activities,
                image_url=row["image_url"],
                price_vnd=row["price_vnd"],
                popularity=row["popularity"],
                source=row["source"],
            ))

        return events

    async def get_by_id(self, event_id: int) -> Optional[Event]:
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

        async with get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, (event_id,))
                row = await cur.fetchone()

        if not row:
            return None

        activities: List[str] = []
        if row["activities"]:
            try:
                activities = json.loads(row["activities"])
            except Exception:
                activities = []

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
            activities=activities,
            image_url=row["image_url"],
            price_vnd=row["price_vnd"],
            popularity=row["popularity"],
            source=row["source"],
        )
