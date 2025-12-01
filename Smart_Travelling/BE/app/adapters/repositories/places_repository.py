from typing import List
from app.domain.entities.place_lite import PlaceLite
from app.domain.entities.Address import Address
from app.infrastructure.database.connectdb import get_db
import json


def row_to_place_lite(row) -> PlaceLite:
    # Map dữ liệu address từ DB -> Entity Address
    addr = Address(
        houseNumber=row["house_number"],
        street=row["street"],
        ward=row["ward"],
        district=row["district"],
        city=row["city"],
        lat=row["lat"],
        lng=row["lng"],
    )

    # tags lưu dạng JSON trong DB → parse sang list[str]
    tags = row.get("tags")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = []

    # Map 1 dòng trong DB -> 1 PlaceLite
    return PlaceLite(
        id=row["id"],
        name=row["name"],
        priceVND=row["priceVND"],
        summary=row["summary"],
        description=row["description"],
        openTime=row["openTime"],
        closeTime=row["closeTime"],
        phone=row["phone"],
        rating=row["rating"],
        reviewCount=row["reviewCount"],
        popularity=row["popularity"],
        image_url=row.get("image_url"),
        tags=tags or [],
        dwell=row.get("dwell"),
        category=row["category"],
        address=addr,
    )


def fetch_place_lites_by_city(city: str) -> List[PlaceLite]:
    """
    Lấy danh sách địa điểm tham quan (category = 'visit') theo thành phố.
    Trả về list[PlaceLite].
    """

    # 1. Lấy connection tới DB
    db = get_db()
    if db is None:
        return []

    cursor = db.cursor(dictionary=True)

    # 2. Viết SQL join places + addresses
    sql = """
    SELECT
        p.id,
        p.name,
        p.priceVND,
        p.summary,
        p.description,
        p.openTime,
        p.closeTime,
        p.phone,
        p.rating,
        p.reviewCount,
        p.popularity,
        p.image_url,
        p.tags,
        p.dwell,
        p.category,
        a.house_number,
        a.street,
        a.ward,
        a.district,
        a.city,
        a.lat,
        a.lng
    FROM places p
    JOIN addresses a ON p.address_id = a.id
    WHERE a.city = %s
      AND p.category = 'visit';
    """

    # 3. Thực thi query
    cursor.execute(sql, (city,))
    rows = cursor.fetchall()

    # 4. Đóng cursor + connection
    cursor.close()
    db.close()

    # 5. Convert từng dòng -> PlaceLite
    return [row_to_place_lite(r) for r in rows]
