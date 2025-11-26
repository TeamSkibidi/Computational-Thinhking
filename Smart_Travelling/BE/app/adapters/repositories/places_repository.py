# repositories/places_repository.py
from typing import List
from app.domain.entities.PlaceLite import PlaceLite
from app.domain.entities.Address import Address
from app.config.settings import IMAGE_BASE_URL

def row_to_place_lite(row) -> PlaceLite:
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
    return PlaceLite(
        id=row["id"],
        name=row["name"],
        priceVnd=row["price_vnd"],
        summary=row["summary"],
        description=row["description"],
        openTime=row["open_time"],   
        closeTime=row["close_time"],
        phone=row["phone"],
        rating=row["rating"],
        reviewCount=row["review_count"],
        popularity=row["popularity"],
        category=row["category"],    
        dwell=row.get("dwell"),        
        imageName=row["image_name"],
        imageUrl=f"{IMAGE_BASE_URL}{row['image_name']}" if row["image_name"] else None,
        tags=row.get("tags"),
        address=addr,
    )

async def fetch_place_lites_by_city(pool, city: str) -> List[PlaceLite]:
    sql = """
    SELECT
        p.id,
        p.name,
        p.price_vnd,
        p.summary,
        p.description,
        p.open_time,
        p.close_time,
        p.phone,
        p.rating,
        p.review_count,
        p.popularity,
        p.category,
        p.image_name,
        p.dwell,  
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
      AND p.category = 'visit';
    """
    rows = await pool.fetch(sql, city)
    return [row_to_place_lite(r) for r in rows]
