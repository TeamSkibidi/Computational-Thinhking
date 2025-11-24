import os
import time


from app.application.services.fetch_service import fetch_from_external_api
from app.application.services.merge_service import merge_api_data
from app.application.services.image_service import download_image


from typing import Any, List
from dotenv import load_dotenv

load_dotenv()

async def get_place_info(query: str) -> dict[str, Any] | List[dict[str, Any]] | None:
    """
    Hàm tổng hợp: nhập vào tên địa điểm -> gọi API -> merge dữ liệu -> tải ảnh -> trả JSON.
    Có thể trả về:
    - None: nếu không tìm thấy
    - dict: nếu chỉ có 1 địa điểm
    - List[dict]: nếu có nhiều địa điểm
    """

    # --- B1: Chuẩn bị tham số query ---
    params = {
        "engine": "google_maps",
        "q": query,
        "hl": "vi",
        "api_key": os.getenv("SERPAPI_KEY"),
    }

    print(f"\n🔍 Đang tìm địa điểm: {query}")

    # --- B2: Gọi API ---
    data = fetch_from_external_api(os.getenv("url"), params)
    
    # 🐛 DEBUG: In ra dữ liệu API trả về
    print(f"📦 [DEBUG] API Response type: {type(data)}")
    if data:
        print(f"📦 [DEBUG] API Response keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        print(f"📦 [DEBUG] API Response (first 500 chars): {str(data)[:500]}")
    
    if not data:
        print("❌ Không lấy được dữ liệu từ SerpAPI.")
        return None

    print("✅ Dữ liệu API hợp lệ, đang xử lý...")

    # --- B3: Merge dữ liệu ---
    place = merge_api_data(data)
    
    # 🐛 DEBUG: In ra kết quả sau merge
    print(f"📦 [DEBUG] After merge_api_data: {type(place)}")
    if place:
        print(f"📦 [DEBUG] Place data: {place}")

    if not place:
        print("❌ Không có địa điểm hợp lệ trong dữ liệu API.")
        return None

    # --- B4: Lưu ảnh ---
    # Xử lý cho cả trường hợp dict và list
    places_to_process = place if isinstance(place, list) else [place]
    
    for p in places_to_process:
        img_url = p.get("imageUrl")
        # Tạo tên file từ tên địa điểm (normalize để tránh ký tự đặc biệt)
        place_name = p.get("name", "unknown").replace(" ", "_").replace("/", "-")
        # Thêm timestamp để tránh trùng lặp
        timestamp = int(time.time())
        img_save_path = f"static/images/{place_name}_{timestamp}.jpg"
        saved_image_path = download_image(img_url, img_save_path)
        p["imageName"] = os.path.basename(saved_image_path)
        p["imageLocalPath"] = saved_image_path

    # --- B5: In thông tin tổng hợp ---
    # print("\n=====================================")
    # print(f"ĐỊA ĐIỂM: {place['name']}")
    # print(f"Giá tham khảo: {place.get('priceVnd', 'Không rõ')} VND")
    # print(f"Giờ mở cửa: {place.get('openTime', 'Không rõ')} - {place.get('closeTime', 'Không rõ')}")
    # print(f"Đánh giá: {place.get('rating', 'Chưa có')} ({place.get('reviewCount', 0)} đánh giá)")
    # print(f"Phổ biến: {place.get('popularity', 'Không có dữ liệu')}")
    # print(f"Điện thoại: {place.get('phone', 'Không rõ')}")
    # print(f"Địa chỉ: {place['address']}")
    # print(f"Ảnh gốc: {place.get('imageUrl', 'Không có ảnh')}")
    # print(f"Ảnh đã lưu: {saved_image_path}")
    # print(f"Mô tả ngắn: {place.get('summary')}")
    # print("=====================================\n")

    # --- B6: Trả về JSON kết quả ---
    return place

