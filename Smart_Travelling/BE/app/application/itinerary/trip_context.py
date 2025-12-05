from dataclasses import dataclass
from datetime import date
from typing import List, Optional   
from app.api.schemas.itinerary_request import ItineraryRequest
from app.utils.time_utils import time_to_min
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
        if (req.morning.enabled is False):
            req.morning.start = None
            req.morning.end = None
        if (req.lunch.enabled is False):
            req.lunch.start = None
            req.lunch.end = None
        if (req.afternoon.enabled is False):
            req.afternoon.start = None
            req.afternoon.end = None
        if (req.dinner.enabled is False):
            req.dinner.start = None
            req.dinner.end = None
        if (req.evening.enabled is False):
            req.evening.start = None
            req.evening.end = None
        
        return cls(
            city=req.city,
            date=req.start_date,
            morning_start=time_to_min(req.morning.start) if req.morning.start else None,
            morning_end=time_to_min(req.morning.end) if req.morning.end else None,
            lunch_start=time_to_min(req.lunch.start) if req.lunch.start else None,
            lunch_end=time_to_min(req.lunch.end) if req.lunch.end else None,
            afternoon_start=time_to_min(req.afternoon.start) if req.afternoon.start else None,
            afternoon_end=time_to_min(req.afternoon.end) if req.afternoon.end else None,
            dinner_start=time_to_min(req.dinner.start) if req.dinner.start else None,
            dinner_end=time_to_min(req.dinner.end) if req.dinner.end else None,
            evening_start=time_to_min(req.evening.start) if req.evening.start else None,
            evening_end=time_to_min(req.evening.end) if req.evening.end else None,
            max_places_per_block=req.max_places_per_block,
            max_leg_distance_km=req.max_leg_distance_km,
            preferences=prefs,
            must_visit_place_ids=req.must_visit_place_ids,
            avoid_place_ids=req.avoid_place_ids,
        )
