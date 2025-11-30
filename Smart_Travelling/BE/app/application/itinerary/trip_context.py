from dataclasses import dataclass
from datetime import date

from typing import List, Optional   
from app.api.schemas.itinerary_request import ItineraryRequest
from app.config.setting import (
    MAX_PLACES_PER_BLOCK_DEFAULT,
    MAX_LEG_DISTANCE_KM_DEFAULT,
)

""" tag cho địa điểm """
@dataclass
class UserPreferences:
    preferred_tags: List[str]
    avoid_tags: List[str]

@dataclass
class TripContext:
    city: str
    date: date

    """Thời gian bắt đầu và kết thúc của một buổi tham quan"""
    morning_start: int
    morning_end: int
    afternoon_start: int
    afternoon_end: int
    evening_start: int
    evening_end: int

    """Thời gian ăn uống trong ngày(Buổi trưa, buổi tối)"""
    lunch_start: int
    lunch_end: int
    dinner_start: int
    dinner_end: int

    max_places_per_block: int
    max_leg_distance_km: float

    """ Sở thích người dùng (nếu có) """
    preferences: Optional[UserPreferences]
    must_visit_place_ids: List[int]
    avoid_place_ids: List[int]
    

    """ Tạo TripContext từ ItineraryRequest """
    @classmethod
    def from_request(cls, req: ItineraryRequest) -> "TripContext":
        prefs = None
        if req.preferred_tags or req.avoid_tags:
            prefs = UserPreferences(
                preferred_tags=req.preferred_tags,
                avoid_tags=req.avoid_tags,
            )

        return cls(
            city=req.city,
            date=req.start_date,
            morning_start=7*60 + 30,
            morning_end=11*60,
            lunch_start=11*60 + 30,
            lunch_end=13*60,
            afternoon_start=13*60 + 30,
            afternoon_end=17*60 + 30,
            dinner_start=18*60,
            dinner_end=19*60 + 30,
            evening_start=19*60 + 30,
            evening_end=21*60,
            max_places_per_block=req.max_places_per_block,
            max_leg_distance_km=req.max_leg_distance_km,
            preferences=prefs,
            must_visit_place_ids=req.must_visit_place_ids,
            avoid_place_ids=req.avoid_place_ids,
        )
