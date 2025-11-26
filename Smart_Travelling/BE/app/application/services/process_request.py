from typing import List, Dict
import asyncio

from app.domain.entities.place_lite import PlaceLite  # hoặc place_lite nếu tên file là snake_case
from app.application.interfaces.place_repository import IPlaceRepository
from app.application.services.search_place import search_places
from app.application.services.place_pipeline import get_place_info


def parse_places (data:List[dict]) -> List[PlaceLite]:
    # model_validate giup kiem tra va chuyen doi dict sang model hop le
    return [PlaceLite.model_validate(item) for item in data]

async def process_request(repo: IPlaceRepository, province: str, required_count: int) -> List[PlaceLite]:
    # 1️⃣ Tìm trong Database theo keyword
    db_results: List[PlaceLite] = await repo.find_by_keyword(province)
    print(f"[Database] Đã tìm thấy {len(db_results)} kết quả theo keyword")

    # 🟢 TH1: Database đủ dữ liệu
    if len(db_results) >= required_count:
        print("🟢 TH1: Database đủ dữ liệu")
        return db_results[:required_count]

    # 🟠 TH2 + 🔴 TH3: Database thiếu hoặc rỗng
    needed_count = required_count - len(db_results)
    if db_results:
        print(f"🟠 TH2: Database có {len(db_results)}, cần thêm {needed_count}")
    else:
        print(f"🔴 TH3: Database rỗng, cần tìm {needed_count}")
        
    # 1.5️⃣ KHÔNG thêm địa điểm nổi tiếng - chỉ gọi AI để tìm địa điểm liên quan
    famous_places: List[PlaceLite] = []
    
    # Bỏ qua phần thêm famous places
    # if len(db_results) < required_count:
    #     ... (code cũ)
    
    # Nếu đã đủ (không cần AI)
    if len(db_results) >= required_count:
        print(f"[FINAL] Đủ dữ liệu: {len(db_results)} địa điểm")
        return db_results[:required_count]


    # 2️⃣ Gọi AI để tạo tên địa điểm
    ai_place_names: List[str] = await search_places(db_results, province, needed_count)
    print(f"[AI] Gợi ý {len(ai_place_names)} tên địa điểm")
    print(f"🤖 [AI Raw Response]: {ai_place_names}")

    # 3️⃣ Gọi API song song để lấy thông tin chi tiết
    # Extract name string từ dict nếu cần
    place_names = []
    for item in ai_place_names:
        if isinstance(item, dict):
            name = item.get('name') or item.get('ten_dia_diem', '')
            place_names.append(name)
            print(f"  ✅ Extracted: {name}")
        else:
            place_names.append(str(item))
            print(f"  ➡️ Direct: {item}")
    
    print(f"🎯 [Final Search Terms]: {place_names}")
    tasks = [get_place_info(name) for name in place_names if name]
    results = await asyncio.gather(*tasks, return_exceptions=True)


    new_places_from_api: List[dict] = []
    for r in results:
        if isinstance(r, Exception) or not r:
            continue
        if isinstance(r, dict):
            new_places_from_api.append(r)
        else:
            new_places_from_api.extend(r)

    print(f"[API] Thu thập {len(new_places_from_api)} bản ghi từ API")

    new_models: List[PlaceLite] = []
    for d in new_places_from_api:
        try:
            new_models.append(PlaceLite.model_validate(d))
        except Exception as e:
            print(f"[WARN] Bỏ qua bản ghi không hợp lệ: {e}")

    # 6) Lưu DB (khuyến nghị implement save_place là upsert/insert-ignore)
    for m in new_models:
        try:
            await repo.save(m)
        except Exception as e:
            print(f"[WARN] Lưu thất bại '{m.name}': {e}")

    # 7) Trả về đủ required_count (kết hợp: keyword + API)
    all_results = db_results + new_models
    print(f"[FINAL] Tổng cộng: {len(db_results)} keyword + {len(new_models)} API = {len(all_results)} địa điểm")
    return all_results[:required_count]




# 🔴 TH3: Database hoàn toàn rỗng
    # if not database_result :
    #     all_places: List[PlaceLite] = []
    #     # Duyệt qua vòng lặp để call API theo yêu cầu
    #     for i in range (required_count):
    #         api_result = await search_APITH3 (province) # BUGS : name khong xac dinh
    #         if not api_result:
    #             break 
    #         all_places.append (api_result)
    #         if (len (api_result) >= required_count):
    #             break

    #     all_places = all_places[:required_count] # lấy đủ yêu cầu

    #     if all_places:
    #         await save_to_Database (all_places)

    #     place = parse_places(all_places)
    #     return place
