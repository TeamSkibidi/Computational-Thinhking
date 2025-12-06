import json
from typing import Optional
import pymysql
from dotenv import load_dotenv
import os
import re

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
    if not coord_str or coord_str.upper() == "NULL" or coord_str.strip() == "":
        return None, None
    try:
        parts = coord_str.split(",")
        lat = float(parts[0].strip())
        lng = float(parts[1].strip())
        return lat, lng
    except:
        return None, None


def parse_value(value: str) -> Optional[str]:
    if not value or value.upper() == "NULL" or value.strip() == "" or value == "x":
        return None
    return value.strip()


def parse_tags(tags_str: str) -> list:
    if not tags_str or tags_str.upper() == "NULL" or tags_str.strip() == "":
        return []
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    return tags


def parse_time(time_str: str) -> Optional[str]:
    """Parse time string to HH:MM format (CHAR(5))."""
    if not time_str or time_str.strip() == "" or time_str.upper() == "NULL":
        return None
    
    time_str = time_str.strip()
    
    if time_str == "24:00":
        return "23:59"
    
    if ":" in time_str:
        parts = time_str.split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            if hour >= 24:
                hour = 23
                minute = 59
            return f"{hour:02d}:{minute:02d}"
        except:
            return None
    
    return None


def parse_rating(rating_str: str) -> Optional[float]:
    """Parse rating - DECIMAL(3,2) range 0-5."""
    if not rating_str or rating_str.upper() == "NULL" or rating_str.strip() == "":
        return None
    try:
        rating_str = rating_str.replace(",", ".").strip()
        rating = float(rating_str)
        return round(min(max(rating, 0), 5), 2)
    except:
        return None


def parse_int(value_str: str) -> Optional[int]:
    if not value_str or value_str.upper() == "NULL" or value_str.strip() == "":
        return None
    try:
        clean = re.sub(r'[,.]', '', value_str.strip())
        return int(clean)
    except:
        return None


def parse_price(price_str: str) -> Optional[int]:
    """Parse price - BIGINT >= 0."""
    if not price_str or price_str.upper() == "NULL" or price_str.strip() == "":
        return None
    try:
        clean = price_str.replace(",", "").replace(".", "").strip()
        match = re.search(r'\d+', clean)
        if match:
            price = int(match.group())
            return max(price, 0)
        return None
    except:
        return None


def get_next_address_id(cursor) -> int:
    """Lấy ID tiếp theo cho bảng addresses."""
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM addresses")
    return cursor.fetchone()[0]


def get_next_food_id(cursor) -> int:
    """Lấy ID tiếp theo cho bảng food."""
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM food")
    return cursor.fetchone()[0]


def create_address(cursor, address_id: int, house_number: str, street: str, ward: str, 
                   district: str, city: str, lat: float, lng: float) -> bool:
    """Insert address với ID cụ thể."""
    try:
        sql = """
            INSERT INTO addresses (id, house_number, street, ward, district, city, lat, lng)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            address_id,
            house_number,
            street,
            ward,
            district,
            city or "Hồ Chí Minh",
            lat,
            lng
        ))
        return True
    except Exception as e:
        print(f"  ⚠️ Error creating address {address_id}: {e}")
        return False


def create_food(cursor, food_id: int, food_data: dict, address_id: int) -> bool:
    """Insert food với ID cụ thể."""
    try:
        sql = """
            INSERT INTO food (
                id, name, priceVND, summary, description, 
                openTime, closeTime, phone, rating, reviewCount, 
                popularity, image_url, tags, category, address_id
            ) VALUES (
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s
            )
        """
        
        # Convert tags to JSON string
        tags_json = json.dumps(food_data["tags"], ensure_ascii=False) if food_data["tags"] else None
        
        cursor.execute(sql, (
            food_id,
            food_data["name"],
            food_data["priceVND"],
            food_data["summary"],
            food_data["description"],
            food_data["openTime"],
            food_data["closeTime"],
            food_data["phone"],
            food_data["rating"],
            food_data["reviewCount"],
            food_data["popularity"],
            food_data["image_url"],
            tags_json,
            "eat",
            address_id,
        ))
        return True
    except Exception as e:
        print(f"  ❌ Error creating food {food_id}: {e}")
        return False


def parse_line(line: str) -> Optional[dict]:
    """
    Parse TSV line theo thứ tự cột trong file food.tsv:
    0: id (skip - auto increment)
    1: name
    2: sumary -> summary
    3: desciption -> description
    4: rating
    5: reviewCount
    6: popularity
    7: tags
    8: openTime
    9: closeTime
    10: priceVND
    11: houseNumber
    12: street
    13: ward
    14: district
    15: city
    16: Tọa độ -> lat, lng
    17: URL (skip)
    18: phone
    19: Img name (skip)
    20: Img url -> image_url
    21: dwell (skip)
    """
    parts = line.split("\t")
    
    if len(parts) < 10:
        return None
    
    try:
        # Column 1: name (NOT NULL)
        name = parse_value(parts[1]) if len(parts) > 1 else None
        if not name or name.lower() == "name":  # Skip header
            return None
        
        # Column 2: summary (VARCHAR 160)
        summary = parse_value(parts[2]) if len(parts) > 2 else None
        if summary and len(summary) > 160:
            summary = summary[:157] + "..."
        
        # Column 3: description (TEXT)
        description = parse_value(parts[3]) if len(parts) > 3 else None
        
        # Column 4: rating (DECIMAL 3,2 - range 0-5)
        rating = parse_rating(parts[4]) if len(parts) > 4 else None
        
        # Column 5: reviewCount (INT >= 0)
        review_count = parse_int(parts[5]) if len(parts) > 5 else 0
        if review_count is not None:
            review_count = max(review_count, 0)
        
        # Column 6: popularity (INT 0-100)
        popularity = parse_int(parts[6]) if len(parts) > 6 else 0
        if popularity is not None:
            popularity = min(max(popularity, 0), 100)
        
        # Column 7: tags (JSON)
        tags = parse_tags(parts[7]) if len(parts) > 7 else []
        
        # Column 8: openTime (CHAR 5)
        open_time = parse_time(parts[8]) if len(parts) > 8 else None
        
        # Column 9: closeTime (CHAR 5)
        close_time = parse_time(parts[9]) if len(parts) > 9 else None
        
        # Column 10: priceVND (BIGINT >= 0)
        price = parse_price(parts[10]) if len(parts) > 10 else None
        
        # Columns 11-15: Address fields
        house_number = parse_value(parts[11]) if len(parts) > 11 else None
        street = parse_value(parts[12]) if len(parts) > 12 else None
        ward = parse_value(parts[13]) if len(parts) > 13 else None
        district = parse_value(parts[14]) if len(parts) > 14 else None
        city = parse_value(parts[15]) if len(parts) > 15 else "Hồ Chí Minh"
        
        # Column 16: Tọa độ -> lat, lng
        coord_str = parts[16] if len(parts) > 16 else ""
        lat, lng = parse_coordinates(coord_str)
        
        # Column 18: phone (VARCHAR 50)
        phone = parse_value(parts[18]) if len(parts) > 18 else None
        if phone and len(phone) > 50:
            phone = phone[:50]
        
        # Column 20: Img url -> image_url (VARCHAR 500)
        image_url = parse_value(parts[20]) if len(parts) > 20 else None
        if image_url and len(image_url) > 500:
            image_url = image_url[:500]
        
        return {
            "name": name,
            "summary": summary,
            "description": description,
            "rating": rating,
            "reviewCount": review_count or 0,
            "popularity": popularity or 0,
            "tags": tags,
            "openTime": open_time,
            "closeTime": close_time,
            "priceVND": price,
            "phone": phone,
            "image_url": image_url,
            # Address fields
            "house_number": house_number,
            "street": street,
            "ward": ward,
            "district": district,
            "city": city or "Hồ Chí Minh",
            "lat": lat,
            "lng": lng,
        }
    except Exception as e:
        print(f"  ⚠️ Error parsing: {e}")
        return None


def import_data(data_lines: list):
    print("🚀 Starting food data import...")
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Lấy ID bắt đầu
    address_id = get_next_address_id(cursor)
    food_id = get_next_food_id(cursor)
    
    print(f"📍 Starting address ID: {address_id}")
    print(f"🍜 Starting food ID: {food_id}")
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for i, line in enumerate(data_lines):
        line = line.strip()
        if not line:
            continue
        
        food_data = parse_line(line)
        if not food_data:
            skip_count += 1
            continue
        
        # Tạo address trước
        addr_success = create_address(
            cursor,
            address_id,
            food_data["house_number"],
            food_data["street"],
            food_data["ward"],
            food_data["district"],
            food_data["city"],
            food_data["lat"],
            food_data["lng"],
        )
        
        if not addr_success:
            error_count += 1
            print(f"❌ Failed to create address for: {food_data['name']}")
            continue
        
        # Tạo food với address_id
        food_success = create_food(cursor, food_id, food_data, address_id)
        
        if food_success:
            success_count += 1
            print(f"✅ [{success_count}] {food_data['name']} (food_id={food_id}, addr_id={address_id})")
            # Tăng ID cho record tiếp theo
            address_id += 1
            food_id += 1
        else:
            error_count += 1
            print(f"❌ Failed: {food_data['name']}")
            # Rollback address nếu food fail
            cursor.execute("DELETE FROM addresses WHERE id = %s", (address_id,))
    
    conn.commit()
    
    # Final count
    cursor.execute("SELECT COUNT(*) FROM food")
    total_food = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM addresses")
    total_addr = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"📊 IMPORT SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Success: {success_count}")
    print(f"⏭️ Skipped: {skip_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📍 Total addresses in DB: {total_addr}")
    print(f"🍜 Total food records in DB: {total_food}")


def main():
    data_file = "food.tsv"
    
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"📂 Found {len(lines)} lines in {data_file}")
    else:
        print(f"❌ File {data_file} not found!")
        return
    
    import_data(lines)


if __name__ == "__main__":
    main()