# ...existing code...
import os
import json
import re
from typing import Optional, Tuple, List

import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "db": os.getenv("DB_NAME", "travel"),
    "charset": "utf8mb4",
}


def parse_coordinates(coord_str: str) -> Tuple[Optional[float], Optional[float]]:
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


def parse_tags(tags_str: str) -> List[str]:
    if not tags_str or tags_str.upper() == "NULL" or tags_str.strip() == "":
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]


def parse_time(time_str: str) -> Optional[str]:
    """Normalize to HH:MM (24h)."""
    if not time_str or time_str.strip() == "" or time_str.upper() == "NULL":
        return None
    s = time_str.strip()
    s = s.replace("AM", "").replace("PM", "").replace("am", "").replace("pm", "").strip()
    if s == "24:00":
        return "23:59"
    if ":" in s:
        parts = s.split(":")
        try:
            hh = int(parts[0])
            mm = int(parts[1])
            hh = max(0, min(hh, 23))
            mm = max(0, min(mm, 59))
            return f"{hh:02d}:{mm:02d}"
        except:
            return None
    return None


def parse_rating(rating_str: str) -> Optional[float]:
    if not rating_str or rating_str.upper() == "NULL" or rating_str.strip() == "":
        return None
    try:
        rating = float(rating_str.replace(",", ".").strip())
        return round(min(max(rating, 0.0), 5.0), 2)
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
    """Take the first numeric part; BIGINT >= 0."""
    if not price_str or price_str.upper() == "NULL" or price_str.strip() == "":
        return None
    try:
        nums = re.findall(r'\d+', price_str.replace(".", "").replace(",", ""))
        if not nums:
            return None
        return int(nums[0])
    except:
        return None


def get_next_address_id(cursor) -> int:
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM addresses")
    return cursor.fetchone()[0]


def get_next_food_id(cursor) -> int:
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM food")
    return cursor.fetchone()[0]


def create_address(cursor, address_id: int, house_number: str, street: str, ward: str,
                   district: str, city: str, lat: float, lng: float) -> bool:
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
    try:
        sql = """
            INSERT INTO food (
                id, name, priceVND, summary, description,
                openTime, closeTime, phone, rating, reviewCount,
                popularity, image_url, tags, category, cuisine_type, menu_url,
                address_id
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s
            )
            ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                priceVND=VALUES(priceVND),
                summary=VALUES(summary),
                description=VALUES(description),
                openTime=VALUES(openTime),
                closeTime=VALUES(closeTime),
                phone=VALUES(phone),
                rating=VALUES(rating),
                reviewCount=VALUES(reviewCount),
                popularity=VALUES(popularity),
                image_url=VALUES(image_url),
                tags=VALUES(tags),
                category=VALUES(category),
                cuisine_type=VALUES(cuisine_type),
                menu_url=VALUES(menu_url),
                address_id=VALUES(address_id)
        """
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
            food_data["cuisine_type"],
            food_data["menu_url"],
            address_id,
        ))
        return True
    except Exception as e:
        print(f"  ❌ Error creating food {food_id}: {e}")
        return False

def parse_line(line: str) -> Optional[dict]:
    """
    TSV order (0-based index):
      0:id (ignored), 1:name, 2:sumary, 3:desciption, 4:rating, 5:reviewCount,
      6:popularity, 7:tags, 8:openTime, 9:closeTime, 10:priceVND,
      11:houseNumber, 12:street, 13:ward, 14:district, 15:city,
      16:coords, 17:URL, 18:phone, 19:Img name, 20:dwell, 21:Img url
    """
    parts = line.split("\t")
    if len(parts) < 11:
        return None
    try:
        name = parse_value(parts[1])
        if not name:
            return None
        summary = parse_value(parts[2]) if len(parts) > 2 else None
        description = parse_value(parts[3]) if len(parts) > 3 else None
        rating = parse_rating(parts[4]) if len(parts) > 4 else None
        review_count = parse_int(parts[5]) if len(parts) > 5 else None
        popularity = parse_int(parts[6]) if len(parts) > 6 else None
        tags = parse_tags(parts[7]) if len(parts) > 7 else []
        open_time = parse_time(parts[8]) if len(parts) > 8 else None
        close_time = parse_time(parts[9]) if len(parts) > 9 else None
        price = parse_price(parts[10]) if len(parts) > 10 else None
        house_number = parse_value(parts[11]) if len(parts) > 11 else None
        street = parse_value(parts[12]) if len(parts) > 12 else None
        ward = parse_value(parts[13]) if len(parts) > 13 else None
        district = parse_value(parts[14]) if len(parts) > 14 else None
        city = parse_value(parts[15]) if len(parts) > 15 else None
        lat, lng = parse_coordinates(parts[16]) if len(parts) > 16 else (None, None)
        phone = parse_value(parts[18]) if len(parts) > 18 else None
        # parts[19] = image name (ignored), parts[20] = dwell (ignored)
        image_url = parse_value(parts[21]) if len(parts) > 21 else None

        return {
            "name": name,
            "summary": summary,
            "description": description,
            "rating": rating,
            "reviewCount": review_count,
            "popularity": popularity,
            "tags": tags,
            "openTime": open_time,
            "closeTime": close_time,
            "priceVND": price,
            "house_number": house_number,
            "street": street,
            "ward": ward,
            "district": district,
            "city": city,
            "lat": lat,
            "lng": lng,
            "phone": phone,
            "image_url": image_url,
            "cuisine_type": None,
            "menu_url": None,
        }
    except Exception as e:
        print(f"  ⚠️ Error parsing line: {e}")
        return None


def import_data(data_lines: list):
    print("🚀 Starting food data import...")
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    address_id = get_next_address_id(cursor)
    food_id = get_next_food_id(cursor)

    success = error = skipped = 0

    for i, line in enumerate(data_lines):
        if i == 0 and "name" in line.lower():
            continue  # skip header
        line = line.strip()
        if not line:
            continue

        food_data = parse_line(line)
        if not food_data:
            skipped += 1
            continue

        # create address
        ok_addr = create_address(
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
        if not ok_addr:
            error += 1
            continue

        ok_food = create_food(cursor, food_id, food_data, address_id)
        if ok_food:
            success += 1
        else:
            error += 1

        address_id += 1
        food_id += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Success: {success}")
    print(f"⏭️ Skipped: {skipped}")
    print(f"❌ Errors: {error}")


def main():
    data_file = "food.tsv"
    if not os.path.exists(data_file):
        print(f"❌ File {data_file} not found!")
        return
    with open(data_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    import_data(lines)


if __name__ == "__main__":
    main()
# ...existing code...