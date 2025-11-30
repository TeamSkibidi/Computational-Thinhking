from typing import Dict
from app.application.itinerary.itineray_engine import build_trip_itinerary
from app.api.schemas.itinerary_request import ItineraryRequest
from app.adapters.repositories.food_repository import fetch_food_places_by_city
from app.adapters.repositories.places_repository import fetch_place_lites_by_city
from app.adapters.repositories.accommodation_repository import fetch_accommodations_by_city
from app.domain.entities.itinerary_spot import place_lite_to_spot, food_place_to_spot, accommodation_to_spot


async def get_trip_itinerary(req: ItineraryRequest):
    """
    Tạo lịch trình chuyến đi dựa trên yêu cầu của người dùng.
    - Lấy dữ liệu địa điểm, ẩm thực, chỗ ở từ user
    - Chuyển đổi dữ liệu thô sang ItinerarySpot
    - Gọi trip engine để xây dựng lịch trình
    """
    #  Lấy dữ liệu từ DB

    
    place_lites    = await fetch_place_lites_by_city(req.city)
    food_places    = await fetch_food_places_by_city(req.city)
    accommodations = await fetch_accommodations_by_city(req.city)
    

    # Convert sang ItinerarySpot
    visit_spots = [place_lite_to_spot(p) for p in place_lites]
    food_spots  = [food_place_to_spot(f) for f in food_places]
    hotel_spots = [accommodation_to_spot(a) for a in accommodations]

    

    # Gọi trip engine
    trip = build_trip_itinerary(
        req=req,
        visit_spots=visit_spots,
        food_spots=food_spots,
        hotel_spots=hotel_spots,
    )

    return trip