from typing import List, Set, Optional, Tuple

from app.adapters.repositories.places_repository import fetch_place_lites_by_city
from app.adapters.repositories import user_repository
from app.domain.entities.place_lite import PlaceLite


def recommend_places_by_city(
    city: str,
    user_id: Optional[int] = None,
    seen_ids: Optional[Set[int]] = None,
    k: int = 5
) -> Tuple[List[PlaceLite], Set[int]]:
    """
    Gợi ý k địa điểm tham quan với cá nhân hóa theo user tags.
    
    Logic:
        1. Lấy user tags (nếu có)
        2. Tính match_score cho mỗi place
        3. Sort theo: match_score (cao → thấp), popularity (cao → thấp)
        4. Lấy top k
        5. Cập nhật seen_ids, reset khi hết
    
    Tham số:
        - city: tên thành phố
        - user_id: ID người dùng (để lấy tags)
        - seen_ids: tập id địa điểm đã được gợi ý
        - k: số lượng địa điểm muốn gợi ý (mặc định 5)

    Trả về:
        (list_place, new_seen_ids)
    """

    # 1. Lấy data từ DB
    places: List[PlaceLite] = fetch_place_lites_by_city(city)

    if not places:
        return [], (seen_ids or set())

    # 2. Chuẩn hoá seen_ids
    if seen_ids is None:
        seen_ids = set()

    # 3. Lấy tags sở thích của user
    user_tags: Set = set()
    if user_id is not None:
        user_tags_list = user_repository.get_user_tags(user_id) or []
        user_tags = set(user_tags_list)

    # 4. Lọc ra những địa điểm chưa từng gợi ý
    remain: List[PlaceLite] = []
    for p in places:
        if p.id is None:
            remain.append(p)
        elif p.id not in seen_ids:
            remain.append(p)

    # 5. Nếu số lượng còn lại < k => reset seen_ids
    if len(remain) < k:
        seen_ids.clear()
        remain = places[:]

    # ===== 6. LOGIC GỢI Ý =====

    if user_tags and len(user_tags) > 0:
        # CÓ USER TAGS: Tính score + sort theo score + popularity
        
        # Tính match_score cho mỗi place
        for place in remain:
            place_tags = set(place.tags or [])
            matching_tags = place_tags & user_tags
            num_matching = len(matching_tags)
            # match_score = số tag trùng / tổng số user tags
            match_score = num_matching / len(user_tags)
            place.match_score = match_score
        
        # SORT theo: match_score (cao → thấp), popularity (cao → thấp)
        remain.sort(
            key=lambda p: (
                getattr(p, 'match_score', 0),  # Score cao nhất được ưu tiên
                p.popularity or 0               # Score bằng → popularity cao nhất
            ),
            reverse=True
        )

    else:
        # KHÔNG CÓ USER TAGS: Lấy top k theo popularity
        remain.sort(key=lambda p: p.popularity or 0, reverse=True)

    # 7. Lấy top k
    picked: List[PlaceLite] = remain[:k]

    # 8. Cập nhật seen_ids
    for p in picked:
        if p.id is not None:
            seen_ids.add(p.id)

    return picked, seen_ids