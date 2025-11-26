from dataclasses import dataclass
from typing import List
from typing import Optional, Tuple
from datetime import timedelta
from app.domain.entities.place_lite import PlaceLite
from app.domain.entities.food_place import FoodPlace
from app.domain.entities.accommodation import Accommodation
from app.domain.entities.nightstay import NightStay
from app.utils.tag_utils import apply_tag_filter, tag_score
from app.application.itinerary.trip_context import TripContext, UserPreferences
from app.utils.geo_utils import haversine_km, estimate_travel_minutes
from app.utils.time_utils import min_to_time_str
from app.domain.entities.itinerary_spot import ItinerarySpot
from app.api.schemas.itinerary_request import ItineraryRequest
from app.config.settings import IMAGE_BASE_URL
from app.api.schemas.itinerary_response import DayItineraryResponse, BlockItemResponse, CostSummaryResponse


@dataclass
class BlockItem:
    order: int
    type: str
    name: str
    start_min: int
    end_min: int
    dwell_min: int
    distance_from_prev_km: float
    travel_from_prev_min: int
    price_vnd: int | None
    image_url: str | None


"""------- Các hàm tiện ích cho gợi ý lịch trình -------"""
""" Hàm xây dựng URL hình ảnh từ tên hình ảnh lưu trong DB """
def build_image_url(image_name: str | None) -> str | None:
    if not image_name:
        return None
    return f"{IMAGE_BASE_URL}{image_name}"

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
def visit_sort_key(spot, prefs, must_ids):
    return (
        1 if spot.id in must_ids else 0,   # must_visit trước
        tag_score(spot, prefs),            # hợp gu hơn
        spot.rating or 0.0,                # rating cao hơn
        spot.popularity or 0,              # phổ biến hơn
    )

"""Hàm set thời gian ở lại 1 địa điểm"""
def estimate_dwell_minutes(spot: ItinerarySpot) -> int:
    if spot.dwell is not None:
        return spot.dwell

    return 90

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

""" Chọn khách sạn cho buổi tối """
def pick_hotel_for_night(
    anchor: Optional[ItinerarySpot],
    hotel_spots: List[ItinerarySpot],
    context: TripContext,
) -> tuple[List[BlockItem], Optional[ItinerarySpot]]:
    items: List[BlockItem] = []

    if not hotel_spots:
        return items, None

    """ Lọc khách sạn theo sở thích người dùng """
    candidates = hotel_spots

    """ Hàm sắp xếp khách sạn theo rating và popularity """
    def _hotel_sort_key(s: ItinerarySpot):
        return (
            s.rating or 0.0,
            s.popularity or 0,
        )

    """ Lọc khách sạn khách sạn """
    candidates = sorted(candidates, key=_hotel_sort_key, reverse=True)

    """"""
    best: Optional[Tuple[ItinerarySpot, float, int]] = None  # spot, dist, travel_min
    best_score: Optional[tuple] = None

    for h in candidates:
        if anchor is not None:
            dist_km = haversine_km(anchor.lat, anchor.lng, h.lat, h.lng)
            # có thể cho hotel xa hơn chút, ví dụ gấp đôi max_leg_distance
            if dist_km > context.max_leg_distance_km * 2:
                continue
            travel_min = estimate_travel_minutes(dist_km)
        else:
            dist_km = 0.0
            travel_min = 0

        # score: rating cao + popularity cao + gần anchor
        score = (
            h.rating or 0.0,
            h.popularity or 0,
            -(dist_km),
        )

        if best is None or score > best_score:
            best = (h, dist_km, travel_min)
            best_score = score

    if best is None:
        return items, None

    hotel_spot, dist_km, travel_min = best

    # xác định thời gian check-in khách sạn:
    # - nếu có anchor: bắt đầu sau khi kết thúc anchor + thời gian di chuyển
    # - nếu không: dùng evening_start
    if anchor is not None:
        # giả sử bạn truyền anchor_end_min từ ngoài, tạm thời dùng context.evening_end
        # nhưng đẹp nhất là truyền vào thời gian kết thúc của block evening
        anchor_end_min = context.evening_end
        start_min = anchor_end_min + travel_min
    else:
        start_min = context.evening_end  # hoặc evening_start, tuỳ bạn
    end_min = start_min   # hotel không cần dwell, dùng 0

    hotel_item = BlockItem(
        order=0,  # sẽ set lại khi append vào block evening
        type="hotel",
        place_id=hotel_spot.id,
        name=hotel_spot.name,
        start_min=start_min,
        end_min=end_min,
        dwell_min=0,
        distance_from_prev_km=dist_km,
        travel_from_prev_min=travel_min,
        price_vnd=int(hotel_spot.price_vnd) if hotel_spot.price_vnd is not None else None,
        image_url=hotel_spot.image_url,
    )

    items.append(hotel_item)
    return items, hotel_spot

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
            image_url=build_image_url(first_place.image_name),
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
                image_url=build_image_url(candidate.image_name),
            )
        )

        used_place_ids.add(candidate.id)
        last_place = candidate
        last_end_time = candidate_end

    return items



""""------- Build lịch trình cho cả ngày và chuyến đi -------"""
""" Xây dựng lịch trình cho 1 ngày """
def build_day_itinerary(
    context: TripContext,
    visit_spots: list[ItinerarySpot],
    food_spots: list[ItinerarySpot],
    hotel_spots: list[ItinerarySpot],
) -> DayItineraryResponse:
    
    """ Loại bỏ những địa điểm mà user không muốn"""
    visit_spots = apply_avoid(visit_spots, context.avoid_place_ids)
    food_spots  = apply_avoid(food_spots, context.avoid_place_ids)
    hotel_spots = apply_avoid(hotel_spots, context.avoid_place_ids)
    
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
    afternoon_items, last_afternoon_spot = build_visit_block(
        block_start_min=context.afternoon_start,
        block_end_min=context.afternoon_end,
        spots_for_block=afternoon_candidates,
        max_places_per_block=context.max_places_per_block,
        max_leg_km=context.max_leg_distance_km,
        context=context,
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
    if evening_candidates:
        evening_items, last_evening_spot = build_visit_block(
            block_start_min=context.evening_start,
            block_end_min=context.evening_end,
            spots_for_block=evening_candidates,
            max_places_per_block=1,   
            max_leg_km=context.max_leg_distance_km,
            context=context,
        )

    """ Chọn khách sạn cho buổi tối"""
    anchor_spot = last_evening_spot or last_lunch_spot or last_afternoon_spot or last_morning_spot

    hotel_items: list[BlockItem] = []
    chosen_hotel: Optional[ItinerarySpot] = None

    if hotel_spots:
        hotel_items, chosen_hotel = pick_hotel_for_night(
            anchor=anchor_spot,
            hotel_spots=hotel_spots,
            context=context,
        )

        """ Thêm khách sạn vào cuối block evening """
        for h in hotel_items:
            h.order = len(evening_items) + 1
            evening_items.append(h)

    """ Tính tổng chi phí tham quan trong ngày """
    all_items = morning_items + lunch_items + afternoon_items + dinner_items +evening_items
    total_attraction_cost = sum(
        i.price_vnd or 0
        for i in all_items
        if i.type == "visit"
    )
    """ Tính tổng chi phí khách sạn trong 1 đêm"""
    total_hotel_cost = sum(
        i.price_vnd or 0
        for i in all_items
        if i.type == "hotel"
    )
    """ Tính tổng chí phí ăn (nếu có) """
    total_food_cost = sum(
        i.price_vnd or 0
        for i in all_items
        if i.type == "eat"
    )

    cost_summary = CostSummaryResponse(
        total_attraction_cost_vnd=total_attraction_cost,
        total_food_cost_vnd=total_food_cost,
        total_hotel_cost_vnd=total_hotel_cost,
        total_trip_cost_vnd=total_attraction_cost + total_food_cost + total_hotel_cost,
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
    hotel_spots: list[ItinerarySpot],
) -> dict:
    """
    Xây dựng lịch trình cho toàn bộ chuyến đi nhiều ngày.

    - Loop i từ 0 -> num_days-1
    - Mỗi ngày:
        + tạo TripContext cho ngày đó (city + date_i + prefs...)
        + build_day_itinerary -> DayItineraryResponse
    - Giữa các ngày:
        + từ block 'evening' tìm BlockItemResponse type='hotel'
        + tạo NightStay (check_in = date_i, check_out = date_i+1)

    Trả về dict để API trả thẳng cho FE.
    """
    days: List[DayItineraryResponse] = []
    night_stays: List[NightStay] = []

    for i in range(req.num_days):
        
        date_i = req.start_date + timedelta(days=i)

        context = TripContext.from_request(req, date_i)

        """" Xây dựng lịch trình cho NGÀY i"""
        day_plan = build_day_itinerary(
            context=context,
            visit_spots=visit_spots,
            food_spots=food_spots,
            hotel_spots=hotel_spots,
        )
        days.append(day_plan)
        """ Lấy thông tin khách sạn cho đêm nếu không phải ngày cuối"""
        if i < req.num_days - 1:
            
            """ Lấy block evening của ngày hiện tại kiểm tra có khách sạn không"""
            evening_block = day_plan.blocks.get("evening", [])
            """ Tìm mục khách sạn trong block evening """
            hotel_item = next(
                (b for b in evening_block if b.type == "hotel"),
                None,
            )
            if hotel_item is not None:
                night_stays.append(
                    NightStay(
                        guest_name="",             
                        summary=hotel_item.name,   
                        check_in=date_i,
                        check_out=date_i + timedelta(days=1),
                        priceVND=hotel_item.price_vnd,
                        num_guest=None,
                        type_guest="",
                    )
                )

    num_nights = max(req.num_days - 1, 0)
    total_hotel_price = sum(ns.priceVND or 0 for ns in night_stays)

    return {
        "city": req.city,
        "start_date": req.start_date,
        "num_days": req.num_days,
        "num_nights": num_nights,
        "total_hotel_price_vnd": total_hotel_price,
        "days": [d.model_dump() for d in days],          
        "night_stays": [ns.to_json() for ns in night_stays],  
    }


