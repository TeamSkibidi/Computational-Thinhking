# repositories/hotel_repository.py
from typing import List
from app.domain.entities.accommodation import Accommodation
from app.domain.entities.Address import Address

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
        address=addr,
    )

async def fetch_accommodations_by_city(pool, city: str) -> List[Accommodation]:
    sql = """
    SELECT
        p.id,
        p.name,
        p.price_vnd,
        p.summary,
        p.phone,
        p.rating,
        p.review_count,
        p.popularity,
        p.capacity,
        p.tags,
        a.house_number,
        a.street,
        a.ward,
        a.district,
        a.city,
        a.lat,
        a.lng,
        a.maps_url
    FROM places p
    JOIN addresses a ON p.address_id = a.id
    WHERE a.city = $1
      AND p.category = 'hotel';
    """
    rows = await pool.fetch(sql, city)
    return [row_to_accommodation(r) for r in rows]
