from dataclasses import dataclass
from typing import List, Set, Optional, Tuple , Dict
from datetime import timedelta
from app.domain.entities.nightstay import NightStay
from app.utils.tag_utils import apply_tag_filter, tag_score
from app.application.itinerary.trip_context import TripContext, UserPreferences
from app.utils.geo_utils import haversine_km, estimate_travel_minutes
from app.utils.time_utils import min_to_time_str
from app.domain.entities.itinerary_spot import ItinerarySpot
from app.api.schemas.itinerary_request import ItineraryRequest
from app.config.setting import IMAGE_BASE_URL
from app.api.schemas.itinerary_response import DayItineraryResponse, BlockItemResponse, CostSummaryResponse
from app.application.ai.hybrid import HybridRecommender, HybridConfig
from app.application.itinerary.trip_context import UserPreferences
import random


@dataclass
class BlockItem:
    order: int
    type: str
    name: str
    place_id: Optional[int]
    start_min: int
    end_min: int
    dwell_min: int
    distance_from_prev_km: float
    travel_from_prev_min: int
    price_vnd: int | None
    image_url: str | None
"""------- Các hàm tiện ích cho gợi ý lịch trình -------"""

def weighted_random_choice(items: list, weights: list, k: int = 1) -> list:
    """
    Chọn ngẫu nhiên có trọng số từ danh sách.
    Trả về list các item được chọn (không lặp).
    """
    if not items or not weights:
        return []
    
    k = min(k, len(items))
    
    # Normalize weights
    total = sum(weights)
    if total == 0:
        weights = [1.0] * len(items)
        total = len(items)
    
    selected = []
    remaining = list(zip(items, weights))
    
    for _ in range(k):
        if not remaining:
            break
        
        # Normalize probabilities
        total_w = sum(w for _, w in remaining)
        if total_w == 0:
            break
        
        # Random choice
        r = random.random() * total_w
        cumulative = 0.0
        chosen_idx = 0
        
        for i, (_, w) in enumerate(remaining):
            cumulative += w
            if r <= cumulative:
                chosen_idx = i
                break
        
        selected.append(remaining[chosen_idx][0])
        remaining.pop(chosen_idx)
    
    return selected

def calculate_cluster_center(spots: List[ItinerarySpot]) -> Tuple[float, float]:
    """Tính tâm của nhóm địa điểm."""
    if not spots:
        return (0.0, 0.0)
    
    avg_lat = sum(s.lat for s in spots) / len(spots)
    avg_lng = sum(s.lng for s in spots) / len(spots)
    return (avg_lat, avg_lng)

def filter_spots_by_cluster(
    spots: List[ItinerarySpot],
    center_lat: float,
    center_lng: float,
    max_radius_km: float
) -> List[ItinerarySpot]:
    """Lọc địa điểm trong bán kính từ tâm."""
    return [
        s for s in spots
        if haversine_km(center_lat, center_lng, s.lat, s.lng) <= max_radius_km
    ]

""" Hàm tính trọng số cho địa điểm tham quan """
def calculate_spot_weight(
    spot: ItinerarySpot,
    prefs: Optional[UserPreferences],
    must_ids: list[int],
    selected_spots: List[ItinerarySpot] = None,
    distance_from_prev: float = 0.0,
    max_leg_km: float = 5.0,
    randomness: float = 0.25
) -> float:
    """
    Tính trọng số cho địa điểm với yếu tố:
    - AI score (nếu có)
    - Rating và popularity
    - Tag matching
    - Diversity (xa các điểm đã chọn trong trip)
    - Distance penalty (gần hơn = tốt hơn)
    - Random factor
    """
    # === AI SCORE ===
    ai_score = 0.0
    if is_ai_ready() and prefs:
        tags = getattr(prefs, 'tags', None) or getattr(prefs, 'preferred_tags', None) or []
        if tags:
            ai_score = get_ai_score(spot.id, tags)
    
    # === BASE SCORES ===
    rating_score = (spot.rating or 3.0) / 5.0
    popularity_score = min((spot.popularity or 0) / 1000, 1.0)
    
    # === TAG MATCHING ===
    t_score = 0.0
    if prefs:
        spot_tags = set(getattr(spot, 'tags', None) or [])
        pref_tags = set(getattr(prefs, 'tags', None) or getattr(prefs, 'preferred_tags', None) or [])
        if spot_tags and pref_tags:
            t_score = len(spot_tags & pref_tags) / max(len(pref_tags), 1)
    
    # === MUST VISIT BONUS ===
    must_bonus = 2.0 if spot.id in must_ids else 0.0
    
    # === DIVERSITY SCORE - Ưu tiên địa điểm KHÁC với những gì đã chọn ===
    diversity_score = 1.0
    if selected_spots:
        # Tính khoảng cách trung bình đến các điểm đã chọn
        avg_dist = sum(
            haversine_km(spot.lat, spot.lng, s.lat, s.lng)
            for s in selected_spots
        ) / len(selected_spots)
        # Địa điểm xa hơn 2km so với trung bình = diversity cao
        diversity_score = min(avg_dist / 2.0, 1.0)
    
    # === DISTANCE PENALTY - Gần hơn = điểm cao hơn ===
    distance_penalty = 1.0
    if distance_from_prev > 0:
        # Penalty tăng dần theo khoảng cách
        distance_penalty = max(1.0 - (distance_from_prev / max_leg_km), 0.2)
    
    # === COMBINE SCORES ===
    # Nếu có AI score thì ưu tiên AI
    if ai_score > 0:
        deterministic_score = (
            ai_score * 0.30 +           # AI recommendation
            rating_score * 0.15 +       # Rating
            t_score * 0.20 +            # Tag match
            diversity_score * 0.15 +    # Diversity trong trip
            distance_penalty * 0.20 +   # Khoảng cách
            must_bonus
        )
    else:
        deterministic_score = (
            rating_score * 0.25 +
            popularity_score * 0.15 +
            t_score * 0.25 +
            diversity_score * 0.15 +
            distance_penalty * 0.20 +
            must_bonus
        )
    
    # === ADD RANDOMNESS ===
    random_factor = random.uniform(1 - randomness, 1 + randomness)
    
    return deterministic_score * random_factor

def sort_spots_diverse(
    spots: list[ItinerarySpot],
    prefs: Optional[UserPreferences],
    must_ids: list[int],
    selected_in_trip: List[ItinerarySpot] = None,
    anchor_spot: ItinerarySpot = None,
    max_leg_km: float = 5.0,
    randomness: float = 0.25
) -> list[ItinerarySpot]:
    """
    Sắp xếp địa điểm với:
    - AI score (ưu tiên cao nhất nếu có)
    - Tag matching
    - Diversity (không chọn gần các điểm đã chọn trong trip)
    - Distance optimization
    - Random factor
    """
    if not spots:
        return []
    
    if selected_in_trip is None:
        selected_in_trip = []
    
    weighted = []
    for spot in spots:
        # Tính khoảng cách từ anchor
        dist = 0.0
        if anchor_spot:
            dist = haversine_km(anchor_spot.lat, anchor_spot.lng, spot.lat, spot.lng)
        
        weight = calculate_spot_weight(
            spot, prefs, must_ids,
            selected_spots=selected_in_trip,
            distance_from_prev=dist,
            max_leg_km=max_leg_km,
            randomness=randomness
        )
        weighted.append((spot, weight))
    
    # Sort by weight (đã có random factor nên mỗi lần khác nhau)
    weighted.sort(key=lambda x: x[1], reverse=True)
    
    return [s for s, _ in weighted]

""" Hàm loại những địa điểm mà user không muốn tránh theo danh sách id"""
def apply_avoid(spots: list[ItinerarySpot],
                avoid_ids: list[int]) -> list[ItinerarySpot]:
    if not avoid_ids:
        return spots

    avoid_set = set(avoid_ids)
    return [
        s for s in spots
        if s.id is None or s.id not in avoid_set
    ]

""" Hàm sắp xếp địa điểm tham quan dựa trên sở thích người dùng """
def visit_sort_key(spot: ItinerarySpot, prefs: UserPreferences, must_ids, use_ai: bool = True):
    """
    Hàm sắp xếp địa điểm - có tích hợp AI.
    Fallback về rule-based nếu AI không available.
    """
    ai_score = 0.0
    
    if use_ai and is_ai_ready():
        tags = []
        if prefs and hasattr(prefs, 'tags') and prefs.tags:
            tags = prefs.tags
        elif prefs and hasattr(prefs, 'preferred_tags') and prefs.preferred_tags:
            tags = prefs.preferred_tags
        
        if tags:
            ai_score = get_ai_score(spot.id, tags)
    
    # Tính tag_score như cũ
    t_score = 0
    if prefs:
        spot_tags = set(getattr(spot, 'tags', None) or [])
        pref_tags = set(getattr(prefs, 'tags', None) or getattr(prefs, 'preferred_tags', None) or [])
        if spot_tags and pref_tags:
            t_score = len(spot_tags & pref_tags)
    
    return (
        1 if spot.id in must_ids else 0,
        ai_score,
        t_score,
        spot.rating or 0.0,
        getattr(spot, 'popularity', 0) or 0,
    )

# Preload AI scores cho tất cả spots
def preload_ai_scores(spots: list, preferred_tags: List[str]):
    """Preload AI scores cho tất cả spots."""
    global _ai_scores_cache
    
    if not is_ai_ready() or not preferred_tags:
        return
    
    try:
        recommendations = _ai_recommender.recommend(
            preferred_tags=preferred_tags,
            top_k=len(spots) + 50
        )
        
        cache_key_suffix = ','.join(sorted(preferred_tags))
        for place, score, _ in recommendations:
            pid = getattr(place, 'id', None) or getattr(place, 'place_id', None)
            if pid:
                cache_key = f"{pid}:{cache_key_suffix}"
                _ai_scores_cache[cache_key] = score
        
        print(f"Preloaded {len(recommendations)} AI scores")
    except Exception as e:
        print(f"Preload failed: {e}")

"""Hàm set thời gian ở lại 1 địa điểm"""
def estimate_dwell_minutes(spot: ItinerarySpot) -> int:
    if spot.dwell_min is not None:
        return spot.dwell_min

    return 90

""" Lấy ID duy nhất của 1 địa điểm """
def get_spot_unique_id(obj) -> str | None:
    """
    Lấy ra ID duy nhất của 1 địa điểm.
    obj có thể là:
    - ItinerarySpot
    - BlockItemResponse (có field .spot)
    """
    if obj is None:
        return None

    """ Nếu là BlockItemResponse có field .spot thì ưu tiên lấy từ đó """
    spot = getattr(obj, "spot", obj)

    """ Thử lấy từ các thuộc tính có thể có """
    for attr in ("spot_id", "place_id", "id"):
        val = getattr(spot, attr, None)
        if val:
            return str(val)

    return None

""" Lấy tập hợp ID của các địa điểm trong 1 ngày """
def get_spot_ids_from_day(day_plan: DayItineraryResponse) -> set[str]:
    ids: set[str] = set()

    """ Giả sử day_plan.blocks là dict[str, list[BlockItemResponse]] """
    for block_items in day_plan.blocks.values():
        for item in block_items:
            uid = get_spot_unique_id(item)
            if uid:
                ids.add(uid)

    return ids

"""" Hàm xoá các địa điểm trùng trong cùng 1 ngày """
def dedup_day_items_by_name(day_plan: DayItineraryResponse,
                            dedup_types: Set[str] | None = None) -> None:
    """
    Xoá các BlockItemResponse trùng tên trong cùng 1 ngày.
    - dedup_types: set các type muốn chống trùng, ví dụ {"visit"} hoặc {"visit", "eat"}
    """
    if dedup_types is None:
        dedup_types = {"visit"}   

    seen_keys: Set[str] = set()


    """ Duyệt qua từng block trong ngày """
    for block_name, items in list(day_plan.blocks.items()):
        new_items = []
        for item in items:

            """ Kiểm tra nếu loại item cần dedup """
            if item.type in dedup_types and item.name:
                key = f"{item.type}:{item.name}"
                if key in seen_keys:

                    """ Đã thấy trùng, bỏ qua mục này """
                    continue
                seen_keys.add(key)
            new_items.append(item)

        day_plan.blocks[block_name] = new_items

""" Lấy địa điểm nổi tiếng nhất trong danh sách địa điểm lấy ratting trước, popularity sau """
def sort_spots_with_tags(
    spots: list[ItinerarySpot],
    prefs: Optional[UserPreferences],
    must_ids: list[int],
) -> list[ItinerarySpot]:
    return sorted(
        spots,
        key=lambda s: visit_sort_key(s, prefs, must_ids),
        reverse=True,
    )


""" Tính tổng chí phí địa điểm tham quan và khách sạn trong ngày """
def recompute_cost_summary_from_blocks(day_plan: DayItineraryResponse) -> None:
    """Tính lại cost_summary dựa trên các block đã được dedupe."""
    all_items = []
    for items in day_plan.blocks.values():
        all_items.extend(items)

    total_attraction_cost = sum(
        (item.price_vnd or 0)
        for item in all_items
        if item.type == "visit"
    )

    """ Tính tổng chi phí ăn uống """
    total_food_cost = sum(
        (item.price_vnd or 0)
        for item in all_items
        if item.type in ("eat", "food")
    )

    day_plan.cost_summary = CostSummaryResponse(
        total_attraction_cost_vnd=total_attraction_cost,
        total_trip_cost_vnd=(
            total_attraction_cost + total_food_cost
        ),
    )

""" Lọc địa điểm phù hợp với giờ mở cửa trong ngày"""
def filter_spots_for_block(
    spots: list[ItinerarySpot],
    block_start_min: int,
    block_end_min: int
) -> list[ItinerarySpot]:
    result = []
    for s in spots:
        if s.open_time_min is None or s.close_time_min is None:
            continue

        if s.open_time_min < block_end_min and s.close_time_min > block_start_min:
            result.append(s)

    return result

""" Chuyển đổi danh sách BlockItem sang BlockItemResponse """
def block_items_to_response(items: List[BlockItem]) -> list[BlockItemResponse]:
    result = []
    for item in items:
        result.append(BlockItemResponse(
            order=item.order,
            type=item.type,
            name=item.name,
            start=min_to_time_str(item.start_min),
            end=min_to_time_str(item.end_min),
            dwell_min=item.dwell_min,
            distance_from_prev_km=round(item.distance_from_prev_km, 2),
            travel_from_prev_min=item.travel_from_prev_min,
            price_vnd=item.price_vnd,
            image_url=item.image_url,
            place_id=item.place_id,
        ))
    return result

"""------- Build cho từng block-------"""
""" Chọn 1 địa điểm ăn uống phù hợp trong khung thời gian và khoảng cách cho phép """
def pick_meal_block(
    anchor: Optional[ItinerarySpot],
    food_spots_for_block: List[ItinerarySpot],
    block_start_min: int,
    block_end_min: int,
    context: TripContext,
    selected_in_trip: List[ItinerarySpot],
) -> tuple[List[BlockItem], Optional[ItinerarySpot]]:
    items: List[BlockItem] = []

    if not food_spots_for_block:
        return items, None

    """ Lọc theo sở thích người dùng """
    filtered = apply_tag_filter(food_spots_for_block, context.preferences)
    if not filtered:
        print("deo lọc theo sở thích dc")
        return items, None
    
    """ Lọc theo thời gian trong block """
    filtered = filter_spots_for_block(
        filtered,
        block_start_min,
        block_end_min,
    )
    if not filtered:
        print("deo sap xep dc")
        return items, None
    
    """ Sắp xếp quán ăn theo sở thích người dùng """
    sorted_foods = sort_spots_diverse(
        filtered,
        prefs=context.preferences,
        must_ids=context.must_visit_place_ids,
        selected_in_trip=selected_in_trip,
        anchor_spot=anchor,
        max_leg_km=context.max_leg_distance_km,
        randomness=0.3
    )
    if not sorted_foods:
        return items, None

    """ Tìm quán ăn phù hợp - chọn từ TOP 3 """
    valid_foods = []
    
    for f in sorted_foods[:10]:  # Check top 10
        if anchor is not None:
            dist_km = haversine_km(anchor.lat, anchor.lng, f.lat, f.lng)
            if dist_km > context.max_leg_distance_km:
                continue
            travel_min = estimate_travel_minutes(dist_km)
        else:
            dist_km = 0.0
            travel_min = 0

        dwell_min = f.dwell_min if f.dwell_min is not None else 60
        start_min = max(block_start_min, block_start_min + travel_min)
        end_min = start_min + dwell_min

        if end_min > block_end_min:
            continue
        
        if f.open_time_min is not None and start_min < f.open_time_min:
            continue
        if f.close_time_min is not None and end_min > f.close_time_min:
            continue

        valid_foods.append({
            'spot': f,
            'dist_km': dist_km,
            'travel_min': travel_min,
            'dwell_min': dwell_min,
        })
        
        if len(valid_foods) >= 3:
            break

    if not valid_foods:
        return items, None

    # Chọn ngẫu nhiên từ top 3 valid (đã được sort theo weight)
    chosen = random.choice(valid_foods[:min(3, len(valid_foods))])
    food_spot = chosen['spot']
    
    start_min = block_start_min + chosen['travel_min']
    end_min = start_min + chosen['dwell_min']

    item = BlockItem(
        order=1, 
        type="eat",
        place_id=food_spot.id,
        name=food_spot.name,
        start_min=start_min,
        end_min=end_min,
        dwell_min=chosen['dwell_min'],
        distance_from_prev_km=chosen['dist_km'],
        travel_from_prev_min=chosen['travel_min'],
        price_vnd=int(food_spot.price_vnd) if food_spot.price_vnd is not None else None,
        image_url=food_spot.image_url,
    )
    items.append(item)

    return items, food_spot

""" Xây dựng 1 block vd 1 buổi sáng tham quan trong ngày """
def build_visit_block(
    block_start_min: int,
    block_end_min: int,
    spots_for_block: List[ItinerarySpot],
    max_places_per_block: int,
    max_leg_km: float,
    context: TripContext,
    selected_in_trip: List[ItinerarySpot] = None,
    anchor_spot: ItinerarySpot = None,
) -> tuple[List[BlockItem], Optional[ItinerarySpot]]:
    items: List[BlockItem] = []
    current_min = block_start_min
    last_spot = anchor_spot
    order = 1
    
    # Lọc spots đã chọn trong trip
    selected_ids = {s.id for s in selected_in_trip}
    available_spots = [s for s in spots_for_block if s.id not in selected_ids]
    
    if not available_spots:
        return items, last_spot
    
    """ Sắp xếp với đa dạng hóa + AI """
    sorted_spots = sort_spots_diverse(
        available_spots,
        prefs=context.preferences,
        must_ids=context.must_visit_place_ids,
        selected_in_trip=selected_in_trip,
        anchor_spot=anchor_spot,
        max_leg_km=max_leg_km,
        randomness=0.25
    )
    attempts = 0
    max_attempts = len(sorted_spots) * 2  # Cho phép thử nhiều lần
    spot_index = 0
    
    while order <= max_places_per_block and current_min < block_end_min and attempts < max_attempts:
        attempts += 1
        
        if spot_index >= len(sorted_spots):
            # Reset và thử lại với spots còn lại
            break
        
        spot = sorted_spots[spot_index]
        spot_index += 1
        
        # Skip nếu đã chọn
        if spot.id in selected_ids:
            continue
        
        # Tính khoảng cách và thời gian di chuyển
        if last_spot is not None:
            dist_km = haversine_km(last_spot.lat, last_spot.lng, spot.lat, spot.lng)
            if dist_km > max_leg_km * 1.5:  # Nới lỏng một chút
                continue
            travel_min = estimate_travel_minutes(dist_km)
        else:
            dist_km = 0.0
            travel_min = 0
        
        # Tính thời gian bắt đầu và kết thúc
        start_min = current_min + travel_min
        dwell_min = spot.dwell_min if spot.dwell_min else 60
        end_min = start_min + dwell_min
        
        # Check giờ mở cửa
        open_min = spot.open_time_min if spot.open_time_min is not None else 0
        close_min = spot.close_time_min if spot.close_time_min is not None else 1439
        
        # Điều chỉnh start nếu spot chưa mở
        if start_min < open_min:
            start_min = open_min
            end_min = start_min + dwell_min
        
        # Check không vượt quá block end (cho phép vượt 15 phút)
        if start_min >= block_end_min:
            continue
        
        if end_min > block_end_min + 15:
            # Giảm dwell time nếu có thể
            available_time = block_end_min - start_min
            if available_time >= 30:  # Tối thiểu 30 phút
                dwell_min = available_time
                end_min = start_min + dwell_min
            else:
                continue
        
        # Check không vượt quá giờ đóng cửa
        if end_min > close_min:
            continue
        
        # Tạo block item
        item = BlockItem(
            order=order,
            type="visit",
            place_id=spot.id,
            name=spot.name,
            start_min=start_min,
            end_min=end_min,
            dwell_min=dwell_min,
            distance_from_prev_km=round(dist_km, 2),
            travel_from_prev_min=travel_min,
            price_vnd=int(spot.price_vnd) if spot.price_vnd else 0,
            image_url=spot.image_url,
        )
        
        items.append(item)
        selected_ids.add(spot.id)
        last_spot = spot
        current_min = end_min
        order += 1
        
        # Nếu còn nhiều thời gian trống (> 1 giờ), tiếp tục thêm spots
        remaining_time = block_end_min - current_min
        if remaining_time > 60 and order <= max_places_per_block:
            # Tiếp tục vòng lặp
            continue
    
    return items, last_spot

""""------- Build lịch trình cho cả ngày và chuyến đi -------"""
""" Xây dựng lịch trình cho 1 ngày """
def build_day_itinerary(
    context: TripContext,
    visit_spots: list[ItinerarySpot],
    food_spots: list[ItinerarySpot],
    selected_in_trip: List[ItinerarySpot] = None,
) -> DayItineraryResponse:
    
    if selected_in_trip is None:
        selected_in_trip = []
    
    visit_spots = apply_avoid(visit_spots, context.avoid_place_ids)
    food_spots  = apply_avoid(food_spots, context.avoid_place_ids)

    used_visit_place_ids_in_day: set[int] = set()
    selected_today: List[ItinerarySpot] = []

    # XÂY DỰNG CÁC BLOCK TRONG NGÀY
    morning_items: List[BlockItem] = []
    lunch_items: List[BlockItem] = []
    afternoon_items: List[BlockItem] = []
    dinner_items: List[BlockItem] = []
    evening_items: List[BlockItem] = []
    
    last_morning_spot = None
    last_lunch_spot = None
    last_afternoon_spot = None
    last_dinner_spot = None
    last_evening_spot = None

    if (context.morning_start is not None and context.morning_end is not None):
        morning_candidates = filter_spots_for_block(
            visit_spots,
            context.morning_start,
            context.morning_end,
        )
        morning_items, last_morning_spot = build_visit_block(
            block_start_min=context.morning_start,
            block_end_min=context.morning_end,
            spots_for_block=morning_candidates,
            max_places_per_block=context.max_places_per_block,
            max_leg_km=context.max_leg_distance_km,
            context=context,
            selected_in_trip=selected_in_trip + selected_today,
        )

        for item in morning_items:
            spot = next((s for s in visit_spots if s.id == item.place_id), None)
            if spot:
                selected_today.append(spot)
        used_visit_place_ids_in_day.update(
            i.place_id for i in morning_items if i.place_id is not None
        )

    if (context.lunch_start is not None and context.lunch_end is not None):
        lunch_candidates = filter_spots_for_block(
            food_spots,
            context.lunch_start,
            context.lunch_end,
        )

        lunch_items, last_lunch_spot = pick_meal_block(
            anchor=last_morning_spot,
            food_spots_for_block=lunch_candidates,
            block_start_min=context.lunch_start,
            block_end_min=context.lunch_end,
            context=context,
            selected_in_trip=selected_in_trip + selected_today,
        )
        
        for idx, item in enumerate(lunch_items, start=1):
            item.order = idx

    if (context.afternoon_start is not None and context.afternoon_end is not None):
        afternoon_candidates = filter_spots_for_block(
            visit_spots,
            context.afternoon_start,
            context.afternoon_end,
        )
        afternoon_candidates = [
            s for s in afternoon_candidates
            if s.id not in used_visit_place_ids_in_day
        ]
        
        anchor_for_afternoon = last_lunch_spot or last_morning_spot
        
        afternoon_items, last_afternoon_spot = build_visit_block(
            block_start_min=context.afternoon_start,
            block_end_min=context.afternoon_end,
            spots_for_block=afternoon_candidates,
            max_places_per_block=context.max_places_per_block,
            max_leg_km=context.max_leg_distance_km,
            context=context,
            selected_in_trip=selected_in_trip + selected_today,
            anchor_spot=anchor_for_afternoon,
        )
        for item in afternoon_items:
            spot = next((s for s in visit_spots if s.id == item.place_id), None)
            if spot:
                selected_today.append(spot)

        used_visit_place_ids_in_day.update(
            i.place_id for i in afternoon_items if i.place_id is not None
        )

    if (context.dinner_start is not None and context.dinner_end is not None):
        dinner_candidates = filter_spots_for_block(
            food_spots,
            context.dinner_start,
            context.dinner_end,
        )

        dinner_items, last_dinner_spot = pick_meal_block(
            anchor=last_afternoon_spot,
            food_spots_for_block=dinner_candidates,
            block_start_min=context.dinner_start,
            block_end_min=context.dinner_end,
            context=context,
            selected_in_trip=selected_in_trip + selected_today,
        )
        
        for idx, item in enumerate(dinner_items, start=1):
            item.order = idx
    if (context.evening_start is not None and context.evening_end is not None):
        evening_candidates = filter_spots_for_block(
            visit_spots,
            context.evening_start,
            context.evening_end,
        )
        evening_candidates = [
            s for s in evening_candidates
            if s.id not in used_visit_place_ids_in_day
        ]
        
        anchor_for_evening = last_dinner_spot or last_afternoon_spot
        
        evening_items, last_evening_spot = build_visit_block(
            block_start_min=context.evening_start,
            block_end_min=context.evening_end,
            spots_for_block=evening_candidates,
            max_places_per_block=1,
            max_leg_km=context.max_leg_distance_km,
            context=context,
            selected_in_trip=selected_in_trip + selected_today,
            anchor_spot=anchor_for_evening,
        )
        
        for item in evening_items:
            spot = next((s for s in visit_spots if s.id == item.place_id), None)
            if spot:
                selected_today.append(spot)

    # === TÍNH CHI PHÍ ===
    all_items = morning_items + lunch_items + afternoon_items + dinner_items + evening_items
    
    total_attraction_cost = sum(
        i.price_vnd or 0 for i in all_items if i.type == "visit"
    )
    total_food_cost = sum(
        i.price_vnd or 0 for i in all_items if i.type == "eat"
    )

    cost_summary = CostSummaryResponse(
        total_attraction_cost_vnd=total_attraction_cost,
        total_trip_cost_vnd=total_attraction_cost + total_food_cost,
    )

    day_response = DayItineraryResponse(
        city=context.city,
        date=context.date,
        blocks={
            "morning": block_items_to_response(morning_items),
            "lunch": block_items_to_response(lunch_items),
            "afternoon": block_items_to_response(afternoon_items),
            "dinner": block_items_to_response(dinner_items),
            "evening": block_items_to_response(evening_items),
        },
        cost_summary=cost_summary,
    )

    return day_response, selected_today

""" Xây dựng lịch trình cho toàn bộ chuyến đi """
def build_trip_itinerary(
    req: ItineraryRequest,
    visit_spots: list[ItinerarySpot],
    food_spots: list[ItinerarySpot],
) -> dict:
    """
    Xây dựng lịch trình cho toàn bộ chuyến đi nhiều ngày.
    Không lặp lại cùng 1 địa điểm (theo name) ở các NGÀY KHÁC NHAU.
    """
    preferred_tags = req.preferred_tags
            
    if preferred_tags:
        # Preload scores cho tất cả spots
        all_spots = visit_spots + food_spots
        preload_ai_scores(all_spots, preferred_tags)
    
    days: List[DayItineraryResponse] = []

    """ Theo dõi tên địa điểm đã dùng để tránh lặp lại giữa các ngày """
    all_selected_in_trip: List[ItinerarySpot] = []
    used_visit_names: Set[str] = set()
    used_food_names: Set[str] = set()

    """ Xây dựng lịch trình cho từng ngày """
    for i in range(req.num_days):
        date_i = req.start_date + timedelta(days=i)

        context = TripContext.from_request(req)
        context.date = date_i

        # Lọc địa điểm chưa dùng
        filtered_visit_spots = [
            s for s in visit_spots
            if getattr(s, "name", None) not in used_visit_names
        ]
        filtered_food_spots = [
            s for s in food_spots
            if getattr(s, "name", None) not in used_food_names
        ]

        # Build ngày với context của toàn trip
        day_plan, selected_today = build_day_itinerary(
            context=context,
            visit_spots=filtered_visit_spots,
            food_spots=filtered_food_spots,
            selected_in_trip=all_selected_in_trip,
        )

        # Dedup và tính lại chi phí
        dedup_day_items_by_name(day_plan, dedup_types={"visit", "eat"})
        recompute_cost_summary_from_blocks(day_plan)
        
        days.append(day_plan)

        # Cập nhật tracking
        all_selected_in_trip.extend(selected_today)
        
        for block_items in day_plan.blocks.values():
            for item in block_items:
                if item.type == "visit" and item.name:
                    used_visit_names.add(item.name)
                if item.type == "eat" and item.name:
                    used_food_names.add(item.name)

    num_nights = max(req.num_days - 1, 0)

    # Debug log
    print("\n=== TRIP SUMMARY ===")
    for d in days:
        print(f"DAY: {d.date}")
        for block_name, items in d.blocks.items():
            if items:
                total_dist = sum(it.distance_from_prev_km or 0 for it in items)
                print(f"   {block_name}: {[it.name for it in items]} ({total_dist:.1f}km)")

    return {
        "city": req.city,
        "start_date": req.start_date,
        "num_days": req.num_days,
        "num_nights": num_nights,
        "days": [d.model_dump() for d in days],
    }

# Khởi tạo biến singleton cho module recommender
_ai_recommender: Optional['HybridRecommender'] = None
_ai_scores_cache: Dict[str, float] = {}


def init_ai_recommender(places: list, interactions: list = None) -> bool:
    # Khởi tạo singleton 
    global _ai_recommender
    
    try:
        _ai_recommender = HybridRecommender(HybridConfig(
            content_weight=0.5,
            collaborative_weight=0.3,
            popularity_weight=0.2
        ))
        _ai_recommender.fit(places, interactions)
        _ai_recommender.save_models()
        print(f"Module Recommender initialized with {len(places)} places")
        return True
    except Exception as e:
        print(f"Module Recommender init failed: {e}")
        _ai_recommender = None
        return False


def get_ai_recommender():
    """Lấy AI recommender instance."""
    return _ai_recommender

# Kiểm tra module đã sẵn sàng chưa 
def is_ai_ready() -> bool:
    return _ai_recommender is not None and _ai_recommender.is_trained

def get_ai_score(place_id: int, preferred_tags: List[str]) -> float:
    """Lấy AI score cho 1 địa điểm."""
    global _ai_scores_cache
    
    if not is_ai_ready():
        return 0.0
    
    cache_key = f"{place_id}:{','.join(sorted(preferred_tags))}"
    if cache_key in _ai_scores_cache:
        return _ai_scores_cache[cache_key]
    
    score = _ai_recommender.get_place_score(place_id, preferred_tags)
    _ai_scores_cache[cache_key] = score
    return score

def clear_ai_cache():
    """Xóa cache AI scores."""
    global _ai_scores_cache
    _ai_scores_cache = {}