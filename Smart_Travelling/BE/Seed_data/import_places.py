import json
from typing import Optional
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# Database config
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "db": os.getenv("DB_NAME", "travel"),
    "charset": "utf8mb4",
}


def parse_coordinates(coord_str: str) -> tuple:
    if not coord_str or coord_str == "NULL":
        return None, None
    try:
        parts = coord_str.split(",")
        lat = float(parts[0].strip())
        lng = float(parts[1].strip())
        return lat, lng
    except:
        return None, None


def parse_value(value: str) -> Optional[str]:
    if value == "NULL" or value == "" or value == "x":
        return None
    return value


def determine_category(tags: str, name: str) -> str:
    tags_lower = tags.lower() if tags else ""
    name_lower = name.lower() if name else ""
    
    food_keywords = ["nhà hàng", "quán", "ăn", "restaurant", "cafe", "coffee", 
                     "phở", "cơm", "pizza", "ốc", "trà", "tea", "bistro"]
    for kw in food_keywords:
        if kw in tags_lower or kw in name_lower:
            return "eat"
    
    hotel_keywords = ["lưu trú", "khách sạn", "hotel", "resort", "homestay", "nhà khách"]
    for kw in hotel_keywords:
        if kw in tags_lower or kw in name_lower:
            return "hotel"
    
    return "visit"


def parse_tags(tags_str: str) -> list:
    if not tags_str or tags_str == "NULL":
        return []
    tags = [t.strip() for t in tags_str.split(",")]
    return tags


def create_address(cursor, house_number: str, street: str, ward: str, 
                   district: str, city: str, lat: float, lng: float) -> Optional[int]:
    """Insert address and return address_id"""
    if not any([house_number, street, ward, district, city]):
        return None
    
    try:
        sql = """
            INSERT INTO addresses (house_number, street, ward, district, city, lat, lng)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (house_number, street, ward, district, city, lat, lng))
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating address: {e}")
        return None


def create_place(cursor, place_data: dict) -> bool:
    try:
        sql = """
            INSERT INTO places (
                id, name, priceVND, summary, description, 
                openTime, closeTime, phone, rating, reviewCount, 
                popularity, image_url, tags, category, dwell, address_id
            ) VALUES (
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                priceVND = VALUES(priceVND),
                summary = VALUES(summary),
                description = VALUES(description),
                openTime = VALUES(openTime),
                closeTime = VALUES(closeTime),
                phone = VALUES(phone),
                rating = VALUES(rating),
                reviewCount = VALUES(reviewCount),
                popularity = VALUES(popularity),
                image_url = VALUES(image_url),
                tags = VALUES(tags),
                category = VALUES(category),
                dwell = VALUES(dwell),
                address_id = VALUES(address_id)
        """
        
        cursor.execute(sql, (
            place_data["id"],
            place_data["name"],
            place_data["priceVND"],
            place_data["summary"],
            place_data["description"],
            place_data["openTime"],
            place_data["closeTime"],
            place_data["phone"],
            place_data["rating"],
            place_data["reviewCount"],
            place_data["popularity"],
            place_data["image_url"],
            json.dumps(place_data["tags"], ensure_ascii=False),
            place_data["category"],
            place_data["dwell"],
            place_data["address_id"],
        ))
        return True
    except Exception as e:
        print(f"Error creating place {place_data.get('name')}: {e}")
        return False


def parse_line(line: str) -> Optional[dict]:
    parts = line.split("\t")
    
    if len(parts) < 20:
        return None
    
    try:
        place_id = parts[0].strip()
        if not place_id.isdigit():
            return None
        
        coord_str = parts[16] if len(parts) > 16 else ""
        lat, lng = parse_coordinates(coord_str)
        
        tags_str = parts[7] if len(parts) > 7 else ""
        tags = parse_tags(tags_str)
        
        category = determine_category(tags_str, parts[1])
        
        rating = None
        if parts[4] and parts[4] != "NULL":
            try:
                rating = float(parts[4])
            except:
                pass
        
        review_count = None
        if len(parts) > 5 and parts[5] and parts[5] != "NULL":
            try:
                review_count = int(parts[5])
            except:
                pass
        
        popularity = None
        if len(parts) > 6 and parts[6] and parts[6] != "NULL":
            try:
                popularity = int(parts[6])
            except:
                pass
        
        price = None
        if len(parts) > 10 and parts[10] and parts[10] != "NULL":
            try:
                price = int(parts[10])
            except:
                pass
        
        dwell = None
        if len(parts) > 20 and parts[20] and parts[20] != "NULL":
            try:
                dwell = int(parts[20])
            except:
                pass
        
        # Parse address - Column 11 là house_number, 12 là street
        house_number = parse_value(parts[11]) if len(parts) > 11 else None
        street = parse_value(parts[12]) if len(parts) > 12 else None
        ward = parse_value(parts[13]) if len(parts) > 13 else None
        district = parse_value(parts[14]) if len(parts) > 14 else None
        city = parse_value(parts[15]) if len(parts) > 15 else None  # province -> city
        
        return {
            "id": int(place_id),
            "name": parts[1].strip(),
            "summary": parse_value(parts[2]) if len(parts) > 2 else None,
            "description": parse_value(parts[3]) if len(parts) > 3 else None,
            "rating": rating,
            "reviewCount": review_count,
            "popularity": popularity,
            "tags": tags,
            "openTime": parse_value(parts[8]) if len(parts) > 8 else None,
            "closeTime": parse_value(parts[9]) if len(parts) > 9 else None,
            "priceVND": price,
            "house_number": house_number,
            "street": street,
            "ward": ward,
            "district": district,
            "city": city,
            "lat": lat,
            "lng": lng,
            "phone": parse_value(parts[18]) if len(parts) > 18 else None,
            "dwell": dwell,
            "image_url": parse_value(parts[21]) if len(parts) > 21 else None,
            "category": category,
            "address_id": None,
        }
    except Exception as e:
        print(f"Error parsing line: {e}")
        return None


def import_data(data_lines: list):
    print("Starting data import...")
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear old data first
    print("Clearing old data...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DELETE FROM places")
    cursor.execute("DELETE FROM addresses")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    
    success_count = 0
    error_count = 0
    
    for line in data_lines:
        line = line.strip()
        if not line:
            continue
        
        place_data = parse_line(line)
        if not place_data:
            continue
        
        # Create address first
        address_id = create_address(
            cursor,
            place_data["house_number"],
            place_data["street"],
            place_data["ward"],
            place_data["district"],
            place_data["city"],
            place_data["lat"],
            place_data["lng"],
        )
        place_data["address_id"] = address_id
        
        if create_place(cursor, place_data):
            success_count += 1
            print(f"Imported: {place_data['name']}")
        else:
            error_count += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\nImport completed!")
    print(f"  Success: {success_count}")
    print(f" Errors: {error_count}")


def main():
    data_file = "places.tsv"
    
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        print(f"❌ File {data_file} not found!")
        return
    
    import_data(lines)


if __name__ == "__main__":
    main()