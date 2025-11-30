from typing import List
from app.domain.entities.place_lite import PlaceLite
from app.domain.entities.Address import Address
from app.infrastructure.database.connectdb import get_db
from app.config.setting import IMAGE_BASE_URL
import json

def row_to_place_lite(row) -> PlaceLite:
    addr = Address(
        houseNumber=row["house_number"],
        street=row["street"],
        ward=row["ward"],
        district=row["district"],
        city=row["city"],
        lat=row["lat"],
        lng=row["lng"],
        url=row.get("url"),
    )
    tags = row.get("tags")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = []
    return PlaceLite(
        id=row["id"],
        name=row["name"],
        priceVnd=row["priceVND"],
        summary=row["summary"],
        description=row["description"],
        openTime=row["openTime"],   
        closeTime=row["closeTime"],
        phone=row["phone"],
        rating=row["rating"],
        reviewCount=row["reviewCount"],
        popularity=row["popularity"],
        category=row["category"],    
        dwell=row.get("dwell"),        
        imageUrl=f"{IMAGE_BASE_URL}{row['image_name']}" if row["image_name"] else None,
        tags=tags or [],
        address=addr,
    )
async def fetch_place_lites_by_city(city: str) -> List[PlaceLite]:
    
     # Lấy connection đến database
    db = get_db()
    if db is None:
        return []

    cursor = db.cursor(dictionary=True)
    
    
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
        p.category,
        p.image_url,
        p.dwell,  
        p.tags,    
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
    cursor.execute(sql, (city,))

    rows = cursor.fetchall()

    cursor.close()
    db.close()

    return [row_to_place_lite(r) for r in rows]
