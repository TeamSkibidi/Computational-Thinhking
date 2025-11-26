from app.domain.entities.place_lite import PlaceLite
from app.domain.entities.Address import Address
import re
from typing import Any
import math
import os

def merge_api_data(data: dict | None) -> dict | None:
       
    #Duyện qua từng nguồn JSON
    
    # 🐛 DEBUG: In dữ liệu đầu vào
    print(f"🔧 [MERGE DEBUG] Input data type: {type(data)}")
    if data:
        print(f"🔧 [MERGE DEBUG] Input keys: {list(data.keys())[:10]}")  # First 10 keys
    
    if not data:
        print("🔧 [MERGE DEBUG] Data is None or empty!")
        return None    #Nếu dữ liệu trống hoặc None thì bỏ quả
        
        
    #lấy danh sách kết quả từ địa điểm
    local_results = data.get("local_results", []) or data.get("places_results", [])
    print(f"🔧 [MERGE DEBUG] local_results found: {len(local_results) if local_results else 0} items")
    
    # Nếu không có danh sách, thử lấy "place_results" (địa điểm duy nhất)
    if not local_results and data.get("place_results"):
        local_results = [data["place_results"]]   # ép thành list 1 phần tử
        print(f"🔧 [MERGE DEBUG] Using place_results instead")


    if not local_results:
        print(f"🔧 [MERGE DEBUG] No results found! Available keys: {list(data.keys())}")
        return None
    
    # 🔥 FIX: Xử lý TẤT CẢ địa điểm trong local_results
    all_places = []
    
    for idx, item in enumerate(local_results):
        print(f"🔧 [MERGE DEBUG] Processing item {idx+1}/{len(local_results)} with keys: {list(item.keys())[:10]}")
        
        #Lấy các trường cơ bản
        name = item.get("title") or item.get("name")
                
        if not name:
            print(f"⚠️  Skipping item {idx+1}: No name found")
            continue    #bỏ qua nếu không có tên
                
        # --- Địa chỉ ---
        # Lấy thông tin địa chỉ
        address = parse_address(item)
                
                # Ưu tiên chọn hình ảnh
        image_url = (
            item.get("thumbnail")
            or item.get("image")
            or (item.get("photos") or [{}])[0].get("thumbnail")
        )
                
                
        place = PlaceLite(
            id=None,  
            name=name,
            priceVnd=item.get("price_vnd") or item.get("price") or None,
            summary=item.get("summary"),
            description=item.get("description"),
            openTime=item.get("open_time") or item.get("hours", {}).get("open"),
            closeTime=item.get("close_time") or item.get("hours", {}).get("close"),
            phone=item.get("phone"),
            rating=float(item.get("rating")) if item.get("rating") else None,
            reviewCount=item.get("review_count") or item.get("reviews"),
            popularity=calc_popularity(float(item.get("rating")) if item.get("rating") else None, item.get("review_count") or item.get("reviews")),
            imageName=None,
            imageUrl=image_url,
            address=address
        )
        
        all_places.append(place.model_dump())
    
    # Trả về list nếu có nhiều địa điểm, 1 dict nếu chỉ có 1
    if len(all_places) == 0:
        return None
    elif len(all_places) == 1:
        return all_places[0]
    else:
        return all_places

def calc_popularity(rating: float | None, review_count: int | None) -> int | None:
    """
    Tính chỉ số độ phổ biến (popularity) của địa điểm.
    -------------------------------------------------
    Mô hình được tham khảo và điều chỉnh từ:
      - Scoring Popularity in GitHub (Academia.edu, 2022)
      - Metrics for Popularity Bias in Recommender Systems (arXiv:2310.08455, 2023)
      - Multi-Criteria Decision Analysis (Springer, 2024)

    Công thức tổng quát:
        popularity = 100 * ( w_r * R_norm + w_c * C_norm )

    Trong đó:
        R_norm = rating / 5                           # Chuẩn hóa điểm đánh giá (0–1)
        C_norm = log(1 + review_count) / log(20000)   # Giảm cực trị bằng logarit
        w_r = 0.6   → trọng số cho rating
        w_c = 0.4   → trọng số cho review_count
    """

    # Nếu thiếu dữ liệu thì bỏ qua
    if rating is None or review_count is None:
        return None

    # --- Bước 1: Chuẩn hóa từng tiêu chí ---
    R_norm = rating / 5.0
    C_norm = min(math.log1p(review_count) / math.log(20000), 1.0)

    # --- Bước 2: Tổng hợp trọng số (MCDA) ---
    w_r, w_c = 0.6, 0.4
    score = (w_r * R_norm + w_c * C_norm) * 100

    # --- Bước 3: Giới hạn kết quả (0–100) ---
    return max(0, min(100, round(score)))




def parse_address(item: dict[str, Any]) -> Address:
    """
    Phân tích dữ liệu ra houseNumber, street, ward, district, city
    
    """
    
    raw_address = (
        item.get("formatted_address")
        or item.get("address")
        or item.get("vicinity")
        or ""
    ).strip()
    
    #Lấy định vị gps của địa chỉ
    gps = item.get("gps_coordinates", {})
    lat = gps.get("latitude") or item.get("latitude") or item.get("lat")
    lng = gps.get("longitude") or item.get("longitude") or item.get("lng")
    
    url = (
        item.get("maps_url")
        or item.get("google_maps_url")
        or item.get("link")
        or item.get("url")
    )
    
    # gom mọi khoảng trắng và tab xuống dòng về 1 dấu các, chuỗi sạch
    address_clean = re.sub(r"\s+", " ", raw_address)
    
    # bỏ chữ VietNam(tránh nhần lẫn với City) rồi strip(", ") để bỏ dấu phẩy khoảng trắng dư ở riwaf
    address_clean = address_clean.replace("Vietnam", "").strip(", ")

    parts = []  # tạo danh sách rỗng
    
    # Bước 1: tách chuỗi 'address_clean' theo dấu phẩy
    for p in address_clean.split(","):
        # Bước 2: loại bỏ khoảng trắng dư ở đầu và cuối
        trimmed = p.strip()

        # Bước 3: chỉ thêm vào nếu phần này KHÔNG rỗng
        if trimmed:
            parts.append(trimmed)
            
            
    #khởi tạo mặc định
    house_number = None
    street = None
    ward = None
    district = None
    city = None
    
    # Tách số nhà + tên đường từ phần đầu
    # (\d+\s*): một chuỗi số (số nhà) + khoảng trắng tuỳ ý
    # (.+): phần còn lại (tên đường)
    if len(parts) > 0:
        first = parts[0]
        match = re.match(r"^([0-9A-Za-z/.-]+\s+)(.+)$", first)
        if match:
            house_number = match.group(1).strip()
            street = match.group(2).strip()
        else:
            street = first
            
    #Nhận diện ward/district/city bằng từ khóa
    # Duyệt qua từng phần trong danh sách parts
    for part in parts:
        # Chuyển toàn bộ chữ thành chữ thường để so sánh dễ hơn
        lower = part.lower()

        # Kiểm tra xem phần này có chứa từ khóa "phường", "xã" hoặc "ward" không
        if ("phường" in lower) or ("xã" in lower) or ("ward" in lower):
            ward = part   # Nếu có, gán phần này vào biến ward (phường/xã)
        
        # Nếu không, kiểm tra xem có chứa từ khóa "quận", "huyện" hoặc "district" không
        elif ("quận" in lower) or ("huyện" in lower) or ("district" in lower):
            district = part  # Gán phần này vào biến district (quận/huyện)
        
        # Nếu vẫn chưa khớp, kiểm tra các từ khóa "thành phố", "tỉnh", "city", "province"
        elif ("thành phố" in lower) or ("tỉnh" in lower) or ("city" in lower) or ("province" in lower):
            city = part  # Gán phần này vào biến city (thành phố hoặc tỉnh)
            
    #suy luận nếu không tìm thấy các từ của city như trên
    if not city and len(parts) >= 1:
        city = parts[-1]
        
    #làm sạch dữ liệu llaanf nữa (rút gọn)
    # Gọi hàm clean() cho từng phần của địa chỉ
    house_number = clean(house_number)
    street = clean(street)
    ward = clean(ward)
    district = clean(district)
    city = clean(city)
    
    
    return Address(
        houseNumber=house_number,
        street=street,
        ward=ward,
        district=district,
        city=city,
        lat=lat,
        lng=lng,
        url=url
    )






# Hàm làm sạch chuỗi: bỏ khoảng trắng dư và dấu phẩy thừa
def clean(text: str | None) -> str | None:
    # Nếu giá trị rỗng (None hoặc ""), thì trả lại None luôn
    if not text:
        return None
    
    # Thay mọi khoảng trắng lặp lại (>=2 dấu cách) thành 1 dấu cách
    text = re.sub(r"\s{2,}", " ", text)
    
    # Loại bỏ dấu phẩy và khoảng trắng dư ở đầu hoặc cuối
    text = text.strip(", ")
    
    # Trả về chuỗi đã làm sạch
    return text




def get_next_id(prefix="phu_", file_path="id_counter.txt"):
    # Nếu chưa có file → bắt đầu từ 0
    if not os.path.exists(file_path):
        last_id = 0
    else:
        with open(file_path, "r") as f:
            content = f.read().strip()
            last_id = int(content) if content.isdigit() else 0

    # Tăng và lưu lại
    next_id = last_id + 1
    with open(file_path, "w") as f:
        f.write(str(next_id))

    # Trả ID định dạng
    return f"{prefix}{next_id:02d}"

