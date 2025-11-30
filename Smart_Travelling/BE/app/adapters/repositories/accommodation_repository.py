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
        url=row.get("maps_url"),
    )
    return Accommodation(
        name=row["name"],
        capacity=row.get("capacity"),
        priceVND=row["price_vnd"],
        summary=row["summary"],
        phone=row["phone"],
        rating=row["rating"],
        reviewCount=row["review_count"],
        popularity=row["popularity"],
        category="hotel",
        tags=row.get("tags"),
        num_guest=row.get("num_guest"),
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
        h.phone,
        h.rating,
        h.openTime,
        h.closeTime,
        h.reviewCount,
        h.popularity,
        h.capacity,
        h.tags,
        h.category,
        h.image_name,
        h.image_url,
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
