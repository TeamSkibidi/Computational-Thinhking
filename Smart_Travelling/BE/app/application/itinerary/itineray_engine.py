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
    return [
        BlockItemResponse(
            order=i.order,
            type=i.type,
            name=i.name,
            start=min_to_time_str(i.start_min),
            end=min_to_time_str(i.end_min),
            distance_from_prev_km=round(i.distance_from_prev_km, 2),
            travel_from_prev_min=i.travel_from_prev_min,
            dwell_min=i.dwell_min,
            image_url=i.image_url,
            price_vnd=i.price_vnd,
        )
        for i in items
    ]

""" Nối điểm hotel đêm trước với tham quan đầu tiên buổi sáng hôm sau """


"""------- Build cho từng block-------"""
""" Chọn 1 địa điểm ăn uống phù hợp trong khung thời gian và khoảng cách cho phép """
def pick_meal_block(
    anchor: Optional[ItinerarySpot],
    food_spots_for_block: List[ItinerarySpot],
    block_start_min: int,
    block_end_min: int,
    context: TripContext,
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
    sorted_foods = sort_spots_with_tags(
        filtered,
        prefs=context.preferences,
        must_ids=context.must_visit_place_ids,
    )
    if not sorted_foods:
        return items, None

    """ Tìm quán ăn phù hợp nhất """
    best: Optional[Tuple[ItinerarySpot, float, int, int]] = None  
    best_score: Optional[tuple] = None

    """ Duyệt qua các quán ăn đã sắp xếp """
    for f in sorted_foods:
        if anchor is not None:
            dist_km = haversine_km(anchor.lat, anchor.lng, f.lat, f.lng)
            if dist_km > context.max_leg_distance_km:
                continue
            travel_min = estimate_travel_minutes(dist_km)
        else:
            dist_km = 0.0
            travel_min = 0

        """ Thời gian ngồi ăn – V1: 60' """
        dwell_min = f.dwell_min if f.dwell_min is not None else 60

        """ V1 đơn giản: ăn bắt đầu từ block_start + travel """
        start_min = max(block_start_min, (block_start_min + travel_min))
        end_min = start_min + dwell_min

        """ Kiểm tra thời gian kết thúc có vượt quá block không """
        if end_min > block_end_min:
            continue
        
        """ Kiểm tra thời gian mở cửa của quán ăn """
        if f.open_time_min is not None and start_min < f.open_time_min:
            continue
        if f.close_time_min is not None and end_min > f.close_time_min:
            continue

        """" Tính điểm cho quán ăn dựa trên sở thích người dùng và khoảng cách """
        score = (
            visit_sort_key(f, context.preferences, context.must_visit_place_ids),
            -(dist_km),
        )

        if best is None or score > best_score:
            best = (f, dist_km, travel_min, dwell_min)
            best_score = score

    if best is None:
        return items, None

    food_spot, dist_km, travel_min, dwell_min = best
    start_min = block_start_min + travel_min
    end_min = start_min + dwell_min

    item = BlockItem(
        order=1, 
        type="eat",
        place_id=food_spot.id,
        name=food_spot.name,
        start_min=start_min,
        end_min=end_min,
        dwell_min=dwell_min,
        distance_from_prev_km=dist_km,
        travel_from_prev_min=travel_min,
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
) -> tuple[List[BlockItem], Optional[ItinerarySpot]]:
    if not spots_for_block:
        return [], None

    """ Lọc những điểm mà user không muốn"""
    filtered = apply_tag_filter(spots_for_block, context.preferences)
    if not filtered:
        return [], None
    
    """ Sắp xếp địa điểm theo rating và popularity"""
    sorted_spots = sort_spots_with_tags(filtered, prefs=context.preferences, must_ids=context.must_visit_place_ids)
    if not sorted_spots:
        return [], None
    
    """ Tính toán thời gian trong block"""
    block_duration = block_end_min - block_start_min

    # --- place 1 ---
    """ Địa điểm đầu tiên trong ngày(block)"""
    first_place = sorted_spots[0]

    """ Ước lượng thời gian ở lại địa điểm đầu tiên"""
    dwell1 = estimate_dwell_minutes(first_place)

    """ Điều chỉnh thời gian ở lại nếu vượt quá thời gian block"""
    if dwell1 > block_duration:
        dwell1 = int(block_duration * 0.6)

    """ Tạo danh sách các mục trong block"""
    items: List[BlockItem] = []

    """ Thời gian bắt đầu và kết thúc của địa điểm đầu tiên"""
    visit1_start = block_start_min
    visit1_end = visit1_start + dwell1

    """ Thêm địa điểm đầu tiên vào danh sách mục"""
    items.append(
        BlockItem(
            order=1,
            type="visit",
            place_id=first_place.id,
            name=first_place.name,
            start_min=visit1_start,
            end_min=visit1_end,
            dwell_min=dwell1,
            distance_from_prev_km=0.0,
            travel_from_prev_min=0,
            price_vnd=first_place.price_vnd,
            image_url=first_place.image_url,
        )
    )

    """ Theo dõi các địa điểm đã sử dụng"""
    used_place_ids = {first_place.id}
    last_place = first_place
    last_end_time = visit1_end

    # Place 2, 3,....
    """ Thêm địa điểm thứ 2 or thứ 3 nếu thời gian của địa tham quan đầu tiên ngắn """
    while len(items) < max_places_per_block:
        best: Optional[Tuple[ItinerarySpot, float, int, int]] = None
        best_score: Optional[tuple] = None

        for candidate in sorted_spots:
            if candidate.id in used_place_ids:
                continue

            distance_km = haversine_km(
                last_place.lat, last_place.lng,
                candidate.lat, candidate.lng,
            )
            if distance_km > max_leg_km:
                continue

            travel_min = estimate_travel_minutes(distance_km)
            dwell_min = estimate_dwell_minutes(candidate)

            candidate_start = last_end_time + travel_min
            candidate_end = candidate_start + dwell_min

            if candidate_end > block_end_min:
                continue

            """ Kiểm tra giờ mở cửa của địa điểm """                
            if candidate.open_time_min and candidate_start < candidate.open_time_min:
                continue
            if candidate.close_time_min and candidate_end > candidate.close_time_min:
                continue

            score = (
                candidate.rating or 0.0,
                -(distance_km),
                candidate.popularity or 0.0,
            )

            if best is None or score > best_score:
                best = (candidate, distance_km, travel_min, dwell_min)
                best_score = score

        if best is None:
            break

        candidate, distance_km, travel_min, dwell_min = best

        candidate_start = last_end_time + travel_min
        candidate_end = candidate_start + dwell_min
        last_place = candidate
        items.append(
            BlockItem(
                order=len(items) + 1,
                type="visit",
                place_id=candidate.id,
                name=candidate.name,
                start_min=candidate_start,
                end_min=candidate_end,
                dwell_min=dwell_min,
                distance_from_prev_km=distance_km,
                travel_from_prev_min=travel_min,
                price_vnd=candidate.price_vnd,
                image_url=candidate.image_url,
            )
        )

        used_place_ids.add(candidate.id)
        last_place = candidate
        last_end_time = candidate_end

    return items , last_place


""""------- Build lịch trình cho cả ngày và chuyến đi -------"""
""" Xây dựng lịch trình cho 1 ngày """
def build_day_itinerary(
    context: TripContext,
    visit_spots: list[ItinerarySpot],
    food_spots: list[ItinerarySpot],
) -> DayItineraryResponse:
    
    """ Loại bỏ những địa điểm mà user không muốn"""
    visit_spots = apply_avoid(visit_spots, context.avoid_place_ids)
    food_spots  = apply_avoid(food_spots, context.avoid_place_ids)

    used_visit_place_ids_in_day: set[int] = set()

    """ Morning """
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
    )

    used_visit_place_ids_in_day.update(
        i.place_id for i in morning_items if i.place_id is not None
    )


    """ Lunch """
    lunch_candidates = filter_spots_for_block(
        food_spots,
        context.lunch_start,
        context.lunch_end,
    )

    lunch_items: list[BlockItem] = []
    last_lunch_spot: Optional[ItinerarySpot] = None

    if lunch_candidates:
        lunch_items, last_lunch_spot = pick_meal_block(
            anchor=last_morning_spot,
            food_spots=lunch_candidates,
            block_start_min=context.lunch_start,
            block_end_min=context.lunch_end,
            context=context,
        )
        for idx, item in enumerate(lunch_items, start=1):
            item.order = idx

    
    """ Afternoon """
    afternoon_candidates = filter_spots_for_block(
        visit_spots,
        context.afternoon_start,
        context.afternoon_end,
    )
    afternoon_candidates = [
        s for s in afternoon_candidates
        if s.id not in used_visit_place_ids_in_day
    ]
    afternoon_items, last_afternoon_spot = build_visit_block(
        block_start_min=context.afternoon_start,
        block_end_min=context.afternoon_end,
        spots_for_block=afternoon_candidates,
        max_places_per_block=context.max_places_per_block,
        max_leg_km=context.max_leg_distance_km,
        context=context,
    )
    used_visit_place_ids_in_day.update(
        i.place_id for i in afternoon_items if i.place_id is not None
    )

    """ Dinnner"""
    dinner_candidates = filter_spots_for_block(
        food_spots,
        context.dinner_start,
        context.dinner_end,
    )

    dinner_items: list[BlockItem] = []
    last_dinner_spot: Optional[ItinerarySpot] = None

    if dinner_candidates:
        dinner_items, last_dinner_spot = pick_meal_block(
            anchor=last_afternoon_spot,
            food_spots=dinner_candidates,
            block_start_min=context.dinner_start,
            block_end_min=context.dinner_end,
            context=context,
        )
        for idx, item in enumerate(dinner_items, start=1):
            item.order = idx

    """ Evening """
    evening_items: list[BlockItem] = []
    last_evening_spot: Optional[ItinerarySpot] = None

    evening_candidates = filter_spots_for_block(
        visit_spots,
        context.evening_start,
        context.evening_end,
    )
    evening_candidates = [
        s for s in evening_candidates
        if s.id not in used_visit_place_ids_in_day
    ]
    if evening_candidates:
        evening_items, last_evening_spot = build_visit_block(
            block_start_min=context.evening_start,
            block_end_min=context.evening_end,
            spots_for_block=evening_candidates,
            max_places_per_block=1,   
            max_leg_km=context.max_leg_distance_km,
            context=context,
        )
        used_visit_place_ids_in_day.update(
            i.place_id for i in evening_items if i.place_id is not None
        )



    """ Tính tổng chi phí tham quan trong ngày """
    all_items = morning_items + lunch_items + afternoon_items + dinner_items + evening_items
    total_attraction_cost = sum(
        i.price_vnd or 0
        for i in all_items
        if i.type == "visit"
    )
    """ Tính tổng chí phí ăn (nếu có) """
    total_food_cost = sum(
        i.price_vnd or 0
        for i in all_items
        if i.type == "eat"
    )

    cost_summary = CostSummaryResponse(
        total_attraction_cost_vnd=total_attraction_cost,
        total_trip_cost_vnd=total_attraction_cost + total_food_cost,
    )

    return DayItineraryResponse(
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
    preferred_tags = []
    if req.preferred_tags:
        preferred_tags = req.preferred_tags
            
    if preferred_tags:
        # Preload scores cho tất cả spots
        all_spots = visit_spots + food_spots
        preload_ai_scores(all_spots, preferred_tags)
    
    days: List[DayItineraryResponse] = []

    """ Theo dõi tên địa điểm đã dùng để tránh lặp lại giữa các ngày """
    used_visit_names: Set[str] = set()
    used_food_names: Set[str] = set()

    """ Xây dựng lịch trình cho từng ngày """
    for i in range(req.num_days):
        date_i = req.start_date + timedelta(days=i)

        context = TripContext.from_request(req)
        context.date = date_i

        """ helper lọc theo tên đã dùng """
        def keep_visit(spot: ItinerarySpot) -> bool:
            return getattr(spot, "name", None) not in used_visit_names

        def keep_food(spot: ItinerarySpot) -> bool:
            return getattr(spot, "name", None) not in used_food_names

        """ Lọc địa điểm theo tên đã dùng """
        filtered_visit_spots = [s for s in visit_spots if keep_visit(s)]
        filtered_food_spots = [s for s in food_spots if keep_food(s)]

        """ Hotel có thể lặp lại nếu khách ở cùng 1 khách sạn nhiều đêm """

        """ Xây dựng lịch trình cho ngày i """
        day_plan = build_day_itinerary(
            context=context,
            visit_spots=filtered_visit_spots,
            food_spots=filtered_food_spots,
        )

        """ Loại bỏ các địa điểm trùng trong cùng 1 ngày """
        dedup_day_items_by_name(day_plan, dedup_types={"visit", "eat"})

        """ Tính lại tổng chi phí sau khi dedupe """
        recompute_cost_summary_from_blocks(day_plan)
        days.append(day_plan)

        """ Cập nhật danh sách địa điểm đã dùng của các ngày TRƯỚC """
        for block_items in day_plan.blocks.values():
            for item in block_items:

                """ Cập nhật tên địa điểm đã dùng để tránh lặp lại giữa các ngày """
                if item.type == "visit" and item.name:
                    used_visit_names.add(item.name)
                """ Cập nhật tên địa điểm ăn uống đã dùng """
                if item.type == "eat" and item.name:
                    used_food_names.add(item.name)

        """ Lấy thông tin khách sạn buổi tối nếu không phải ngày cuối """

    num_nights = max(req.num_days - 1, 0)

    """ debug để chắc chắn không bị trùng giữa các ngày nữa """
    for d in days:
        print("DAY:", d.date)
        for block_name, items in d.blocks.items():
            print(" ", block_name, "->", [it.name for it in items])

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