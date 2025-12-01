# app/application/services/visitor_service.py

from typing import List, Set, Optional, Tuple
import random

from app.adapters.repositories.places_repository import fetch_place_lites_by_city
from app.domain.entities.place_lite import PlaceLite


def recommend_places_by_city(city: str, seen_ids: Optional[Set[int]] = None, k: int = 5) -> Tuple[List[PlaceLite], Set[int]]:
    """
    Gợi ý k địa điểm tham quan (PlaceLite) theo thành phố, 
    tránh lặp lại những id đã gợi ý trong seen_ids.

    - city: tên thành phố (VD: 'Hồ Chí Minh')
    - seen_ids: tập id địa điểm đã được gợi ý ở các lần trước
    - k: số lượng địa điểm muốn gợi ý (mặc định 5)

    Trả về:
        (list_place, new_seen_ids)
        - list_place: list[PlaceLite] đã chọn
        - new_seen_ids: set[int] đã được cập nhật thêm các id vừa chọn
    """

    # 1. Lấy data từ DB
    places: List[PlaceLite] = fetch_place_lites_by_city(city)

    # Nếu không có dữ liệu thì trả về trống
    if not places:
        return [], (seen_ids or set())

    # 2. Chuẩn hoá seen_ids
    if seen_ids is None:
        seen_ids = set()

    # 3. Lọc ra những địa điểm chưa từng gợi ý
    remain: List[PlaceLite] = []
    for p in places:
        # p.id có thể None (phòng xa), nên check trước
        if p.id is None:
            remain.append(p)
        elif p.id not in seen_ids:
            remain.append(p)

    # 4. Nếu số lượng còn lại < k => reset seen_ids, random lại từ đầu
    if len(remain) < k:
        seen_ids.clear()
        remain = places[:]  # copy toàn bộ list

    # 5. Random chọn k phần tử (hoặc ít hơn nếu dữ liệu ít)
    picked: List[PlaceLite] = random.sample(remain, k=min(k, len(remain)))

    # 6. Cập nhật seen_ids với những id vừa chọn
    for p in picked:
        if p.id is not None:
            seen_ids.add(p.id)

    return picked, seen_ids
