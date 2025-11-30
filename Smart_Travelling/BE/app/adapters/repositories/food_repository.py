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

async def fetch_food_places_by_city(city: str) -> List[FoodPlace]:
    
    # Lấy connection đến database
    db = get_db()
    if db is None:
        return [];

    cursor = db.cursor(dictionary=True)
    
    sql = """
    SELECT
        f.id,
        f.name,
        f.summary,
        f.description,
        f.priceVND,
        f.rating,
        f.reviewCount,
        f.image_url,
        f.popularity,
        f.openTime,
        f.closeTime,
        f.phone,
        f.tags,       
        f.image_name, 
        f.category,
        f.cuisine_type,
        f.menu_url,
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
