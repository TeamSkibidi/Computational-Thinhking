import json
from typing import List
from app.domain.entities.accommodation import Accommodation
from app.infrastructure.database.connectdb import get_db
from app.domain.entities.Address import Address
from app.domain.entities.nightstay import NightStay

def row_to_accommodation(row) -> Accommodation:
    addr = Address(
        houseNumber=row["house_number"],
        street=row["street"],
        ward=row["ward"],
        district=row["district"],
        city=row["city"],
        lat=row["lat"],
        lng=row["lng"],
    )
    tags = row.get("tags")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = []
    return Accommodation(
        name=row["name"],
        priceVND=row["priceVND"],
        summary=row["summary"],
        description=row["description"],
        phone=row["phone"],
        rating=row["rating"],
        reviewCount=row["reviewCount"],
        popularity=row["popularity"],
        image_url=row.get("image_url"),
        tags=tags or [],
        num_guest=row.get("num_guest"),
        capacity=row.get("capacity"),
        category=row["category"],
        address=addr,
    )
async def fetch_accommodations_by_city(city: str) -> List[Accommodation]:
    # Lấy connection đến database
    db = get_db()
    if db is None:
        return [];

    cursor = db.cursor(dictionary=True)
    
    sql = """
    SELECT
        h.id,
        h.name,
        h.priceVND,
        h.summary,
        h.description,
        h.phone,
        h.rating,
        h.reviewCount,
        h.popularity,
        h.capacity,
        h.image_url,
        h.tags,
        h.category,
        h.num_guest,
        a.house_number,
        a.street,
        a.ward,
        a.district,
        a.city,
        a.lat,
        a.lng
    FROM accommodation h
    JOIN addresses a ON h.address_id = a.id
    WHERE a.city = %s
      AND h.category = 'hotel';
    """
    cursor.execute(sql, (city,))

    rows = cursor.fetchall()

    

    cursor.close()
    db.close()
    
    return [row_to_accommodation(r) for r in rows]
