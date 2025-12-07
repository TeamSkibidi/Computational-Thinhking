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
    # tính điểm bằng AI nếu có dựa trên tag của người dùng sẽ so sánh với model hybrid đã train trước đó
    ai_score = 0.0
    if is_ai_ready() and prefs:
        tags = getattr(prefs, 'tags', None) or getattr(prefs, 'preferred_tags', None) or []
        if tags:
            ai_score = get_ai_score(spot.id, tags)
    
    # tính điểm dựa trên rating và popularity
    rating_score = (spot.rating or 3.0) / 5.0
    popularity_score = min((spot.popularity or 0) / 1000, 1.0)
    
    # tính điểm dựa trên tag của người dùng (rule_based khác với cái ai)
    t_score = 0.0
    if prefs:
        spot_tags = set(getattr(spot, 'tags', None) or [])
        pref_tags = set(getattr(prefs, 'tags', None) or getattr(prefs, 'preferred_tags', None) or [])
        if spot_tags and pref_tags:
            t_score = len(spot_tags & pref_tags) / max(len(pref_tags), 1)
    
    # Lọc địa điểm phải đi (Chưa sài đâu)
    must_bonus = 2.0 if spot.id in must_ids else 0.0
    
    # Ưu tiên địa điểm so với các điểm đã chọn trong trip
    diversity_score = 1.0
    if selected_spots:
        # Tính khoảng cách trung bình đến các điểm đã chọn
        avg_dist = sum(
            haversine_km(spot.lat, spot.lng, s.lat, s.lng)
            for s in selected_spots
        ) / len(selected_spots)
        # Địa điểm xa hơn 2km so với trung bình = diversity cao
        diversity_score = min(avg_dist / 2.0, 1.0)
    
    # Chấm điểm khoảng cách gần hơn tốt hơn
    distance_penalty = 1.0
    if distance_from_prev > 0:
        # Penalty tăng dần theo khoảng cách
        distance_penalty = max(1.0 - (distance_from_prev / max_leg_km), 0.2)
    

    # Nếu có AI score thì ưu tiên AI
    if ai_score > 0:
        deterministic_score = (
            ai_score * 0.30 +           
            rating_score * 0.15 +
            t_score * 0.20 +
            diversity_score * 0.15 +
            distance_penalty * 0.20 +
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
    
    # random ngẫu nhiên để tăng tính đa dạng các địa điểm
    random_factor = random.uniform(1 - randomness, 1 + randomness)
    
    return deterministic_score * random_factor

""" Hàm sắp xếp địa điểm tham quan với đa dạng cao """
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
    
    # Tính trọng số cho từng địa điểm
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

""" Hàm lấy AI score cho 1 địa điểm với tag người dùng """
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
    
    """ Lọc theo thời gian trong block """
    filtered = filter_spots_for_block(
        food_spots_for_block,
        block_start_min,
        block_end_min,
    )
    if not filtered:
        print("khong sap xep dc")
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
    """
    Build 1 block tham quan, cố gắng lấp đủ max_places_per_block.
    Co giãn dwell time và nới lỏng khoảng cách hợp lý để tránh thiếu spot.
    """
    items: List[BlockItem] = []
    current_min = block_start_min
    last_spot = anchor_spot
    order = 1

    if selected_in_trip is None:
        selected_in_trip = []

    # Lọc spots đã chọn trong trip (theo id)
    selected_ids = {s.id for s in selected_in_trip if s.id is not None}
    available_spots = [s for s in spots_for_block if s.id not in selected_ids]

    if not available_spots:
        return items, last_spot

    # Sắp xếp ban đầu theo AI + sở thích
    sorted_spots = sort_spots_diverse(
        available_spots,
        prefs=context.preferences,
        must_ids=context.must_visit_place_ids,
        selected_in_trip=selected_in_trip,
        anchor_spot=anchor_spot,
        max_leg_km=max_leg_km,
        randomness=0.25,
    )

    # Pool động (xóa dần các spot đã chọn)
    pool = list(sorted_spots)

    # Lặp để chọn tới max_places_per_block
    while order <= max_places_per_block:
        # Nếu thời gian còn lại quá ít thì dừng
        if current_min >= block_end_min - 30:  # < 30 phút thì thôi
            break

        best = None
        best_score = -1e9

        for idx, spot in enumerate(pool):
            # Khoảng cách & thời gian di chuyển
            if last_spot is not None:
                dist_km = haversine_km(last_spot.lat, last_spot.lng, spot.lat, spot.lng)
                travel_min = estimate_travel_minutes(dist_km)
            else:
                dist_km = 0.0
                travel_min = 0

            # Nới lỏng khoảng cách theo thứ tự spot
            # slot đầu: cho phép đi xa hơn để khởi động
            # slot cuối: cũng nới một chút để vét nốt
            if order == 1:
                dist_limit = max_leg_km * 3.0
            elif order == max_places_per_block:
                dist_limit = max_leg_km * 2.0
            else:
                dist_limit = max_leg_km * 1.5

            if dist_km > dist_limit:
                continue

            start_min = current_min + travel_min

            # Giờ mở/đóng cửa
            open_min = spot.open_time_min if spot.open_time_min is not None else 0
            close_min = spot.close_time_min if spot.close_time_min is not None else 1439

            # Nếu đến trước giờ mở cửa -> phải chờ
            wait = 0
            if start_min < open_min:
                wait = open_min - start_min
                start_min = open_min

            # Nếu phải chờ quá lâu (> 30p) thì bỏ spot này, thử cái khác
            if wait > 30:
                continue

            # Nếu tới nơi đã sau giờ đóng -> bỏ
            if start_min >= close_min:
                continue

            # Thời gian còn lại trong block và tới khi đóng cửa
            time_left_block = block_end_min - start_min
            time_until_close = close_min - start_min
            max_possible_dwell = min(time_left_block, time_until_close)

            # Nếu không đủ tối thiểu 30p cho spot này -> bỏ
            if max_possible_dwell < 30:
                continue

            # dwell chuẩn hoặc co lại cho vừa
            base_dwell = spot.dwell_min if spot.dwell_min is not None else 60
            if base_dwell <= max_possible_dwell:
                dwell = base_dwell
            else:
                dwell = max_possible_dwell  # co lại

            end_min = start_min + dwell

            # Chấm điểm: ưu tiên
            # - ít chờ
            # - gần
            # - rating/popularity cao
            score = 0.0
            score -= wait * 4.0
            score -= dist_km * 15.0
            score += (spot.rating or 3.0) * 8.0
            score += (min((spot.popularity or 0) / 1000, 1.0)) * 5.0

            # Ưu tiên slot cuối để lấp kín
            if order == max_places_per_block:
                score += 20.0

            if score > best_score:
                best_score = score
                best = {
                    "idx": idx,
                    "spot": spot,
                    "start": start_min,
                    "end": end_min,
                    "dwell": int(dwell),
                    "dist": float(dist_km),
                    "travel": int(travel_min),
                }

        # Không tìm được spot hợp lệ cho slot hiện tại -> dừng block
        if best is None:
            break

        chosen = best["spot"]
        item = BlockItem(
            order=order,
            type="visit",
            place_id=chosen.id,
            name=chosen.name,
            start_min=best["start"],
            end_min=best["end"],
            dwell_min=best["dwell"],
            distance_from_prev_km=round(best["dist"], 2),
            travel_from_prev_min=best["travel"],
            price_vnd=int(chosen.price_vnd) if chosen.price_vnd else 0,
            image_url=chosen.image_url,
        )
        items.append(item)

        # Cập nhật trạng thái
        current_min = best["end"]
        last_spot = chosen
        order += 1

        # Xoá spot khỏi pool để không chọn lại
        pool.pop(best["idx"])

        if not pool:
            break

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

        # Tránh trùng lặp địa điểm trong ngày
        dedup_day_items_by_name(day_plan, dedup_types={"visit", "eat"})

        # Cập nhật lại cost summary sau khi dedupe
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

""" Khởi tạo module hybrid recommender AI """
_ai_recommender: Optional['HybridRecommender'] = None
_ai_scores_cache: Dict[str, float] = {}

""" Khởi tạo module hybrid recommender AI """
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

""" Lấy instance của AI recommender """
def get_ai_recommender():
    """Lấy AI recommender instance."""
    return _ai_recommender

""" Kiểm tra module AI recommender đã sẵn sàng chưa """
def is_ai_ready() -> bool:
    return _ai_recommender is not None and _ai_recommender.is_trained

""" Lấy AI score cho 1 địa điểm với tag người dùng """
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

""" Xóa cache AI scores """
def clear_ai_cache():
    """Xóa cache AI scores."""
    global _ai_scores_cache
    _ai_scores_cache = {}