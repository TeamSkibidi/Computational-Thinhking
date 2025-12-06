import json
from typing import List
from app.domain.entities.food_place import FoodPlace
from app.domain.entities.Address import Address
from app.infrastructure.database.connectdb import get_db
from app.config.setting import IMAGE_BASE_URL

def row_to_food_place(row) -> FoodPlace:
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
    return FoodPlace(
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
        cuisine=row.get("cuisine_type"),
        category=row["category"],
        address=addr,
    )

def fetch_food_places_by_city(city: str) -> List[FoodPlace]:
    
    # Lấy connection đến database
    db = get_db()
    if db is None:
        return []

    cursor = db.cursor(dictionary=True)
    
    sql = """
    SELECT
        f.id,
        f.name,
        f.priceVND,
        f.summary,
        f.description,
        f.rating, 
        f.openTime,      
        f.closeTime,
        f.phone,
        f.reviewCount,
        f.popularity,
        f.image_url,
        f.tags,       
        f.category,
        f.cuisine_type,
        a.house_number,
        a.street,
        a.ward,
        a.district,
        a.city,
        a.lat,
        a.lng
    FROM food f
    JOIN addresses a ON f.address_id = a.id
    WHERE a.city = %s
      AND f.category = 'eat';
    """
    cursor.execute(sql, (city,))

    rows = cursor.fetchall()

    
    cursor.close()
    db.close()
    
    return [row_to_food_place(r) for r in rows]
