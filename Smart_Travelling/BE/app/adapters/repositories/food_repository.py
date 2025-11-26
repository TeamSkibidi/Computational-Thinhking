# repositories/food_repository.py
from typing import List
from app.domain.entities.FoodPlace import FoodPlace
from app.domain.entities.Address import Address
# from app.config.settings import IMAGE_BASE_URL

def row_to_food_place(row) -> FoodPlace:
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
    return FoodPlace(
        id=row["id"],
        name=row["name"],
        category="eat",
        summary=row["summary"],
        cuisine=row.get("cuisine"),
        priceVNDPerPerson=row["price_vnd_per_person"],
        rating=row["rating"],
        reviewCount=row["review_count"],
        popularity=row["popularity"],
        openTime=row["open_time"],
        closeTime=row["close_time"],
        phone=row["phone"],
        tags=row.get("tags"),  
        address=addr,
    )

async def fetch_food_places_by_city(pool, city: str) -> List[FoodPlace]:
    sql = """
    SELECT
        p.id,
        p.name,
        p.summary,
        p.cuisine,
        p.price_vnd_per_person,
        p.rating,
        p.review_count,
        p.popularity,
        p.open_time,
        p.close_time,
        p.phone,
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
      AND p.category = 'eat';
    """
    rows = await pool.fetch(sql, city)
    return [row_to_food_place(r) for r in rows]
