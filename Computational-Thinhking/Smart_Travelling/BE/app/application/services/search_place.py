
import os, json, re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
API_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")



async def search_places(danh_sach_dia_diem_da_co: list[str] , ten_dia_diem: str, n: int) -> list[str]:
    prompt = ""

    if (n == 0) or (danh_sach_dia_diem_da_co is None) or len(danh_sach_dia_diem_da_co) == 0:
        prompt = f"""Hãy gợi ý {n} địa điểm du lịch nổi tiếng thực tế ở {ten_dia_diem}, Việt Nam.
        
Trả về JSON array với format: [{{"name": "Tên địa điểm đầy đủ"}}, ...]

Ví dụ cho Hồ Chí Minh: [{{"name": "Dinh Độc Lập"}}, {{"name": "Bến Nhà Rồng"}}, {{"name": "Chợ Bến Thành"}}]
Ví dụ cho Cà Mau: [{{"name": "Mũi Cà Mau"}}, {{"name": "Rừng U Minh Hạ"}}, {{"name": "Chợ Cà Mau"}}]

Chỉ trả về tên địa điểm thực tế, có thể tìm kiếm trên Google Maps."""
    else:
        # Convert PlaceLite objects to string names if needed
        place_names = []
        for item in danh_sach_dia_diem_da_co:
            if isinstance(item, str):
                place_names.append(item)
            elif hasattr(item, 'name'):  # PlaceLite object
                place_names.append(item.name)
            else:
                place_names.append(str(item))
        
        so_dia_diem_can_tim = n - len(danh_sach_dia_diem_da_co)
        prompt = f"""Hãy gợi ý {so_dia_diem_can_tim} địa điểm du lịch nổi tiếng thực tế ở {ten_dia_diem}, Việt Nam.

Không bao gồm các địa điểm sau: {', '.join(place_names)}

Trả về JSON array với format: [{{"name": "Tên địa điểm đầy đủ"}}, ...]

Chỉ trả về tên địa điểm thực tế, có thể tìm kiếm trên Google Maps."""
    
    response = model.generate_content(prompt)
    data = response.text
    try:
        danh_sach_dia_diem_can_tim = json.loads(data)
    except json.JSONDecodeError:
        m = re.search(r"\[[\s\S]*\]|\{[\s\S]*\}", data)  
        danh_sach_dia_diem_can_tim = json.loads(m.group(0))
    return danh_sach_dia_diem_can_tim
