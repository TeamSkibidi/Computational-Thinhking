import json 
from typing import List
from app.infrastructure.database.connectdb import get_db

def row_to_tag(row) -> List[str]:
    tags = row.get("tags")

    if tags is None:
        return []

    # Nếu là chuỗi JSON
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)  
        except json.JSONDecodeError:
            return []

    # Nếu DB trả sẵn list thì ta check tiếp
    if isinstance(tags, list):
        # Ép từng phần tử thành string cho chắc
        return [str(t) for t in tags]

    # Các kiểu khác thì bỏ qua
    return []

def fetch_tags_by_data() -> List[str]:

    # Lấy connection đến database
    db = get_db()
    if db is None:
        return []

    # Tạo con trỏ để thực hiện truy vấn để  lấy tags từ bảng place
    cursor = db.cursor(dictionary=True)
    sql_place = """     SELECT DISTINCT k.tags FROM places k """ 

    # Thực hiện truy vấn để lấy tags từ bảng places 
    cursor.execute(sql_place)
    row_tag_place = cursor.fetchall()


    # Thực hiện truy vấn để lấy tags từ bảng food 
    sql_food = """ SELECT DISTINCT h.tags FROM food h """ 


    # Thực hiện truy vấn để lấy tags từ bảng food 
    cursor.execute(sql_food)
    row_tag_food = cursor.fetchall()


    # Kết hợp kết quả từ hai bảng places và food
    rows = row_tag_place + row_tag_food

    # Loại bỏ các thẻ trùng lặp
    all_tags: List[str] = []
    hash_tags = set()
    
    for row in rows:
        tags = row_to_tag(row)
        for tag in tags:
            if tag not in hash_tags:
                hash_tags.add(tag)
                all_tags.append(tag)

    cursor.close()
    db.close()

    return all_tags