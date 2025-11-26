# itinerary_spot.py

from dataclasses import dataclass
from typing import Optional, Literal

# Chỉnh lại import cho đúng với project của bạn
from .Address import Address
from .place_lite import PlaceLite  # hoặc path tương ứng
from .food_place import FoodPlace
from .accommodation import Accommodation
from app.utils.time_utils import time_str_to_min

@dataclass
class ItinerarySpot:
    """
    Spot nội bộ cho engine:
    - category: 'visit' | 'eat' | 'hotel'
    - lat/lng: để tính khoảng cách
    - open/close: phút trong ngày
    - price_vnd: giá vé / giá bữa / giá 1 đêm
    - dwell_min: thời lượng chơi/ăn gợi ý
    """
    id: Optional[int]
    name: str
    category: Literal["visit", "eat", "hotel"]

    lat: float
    lng: float

    open_time_min: Optional[int] = None
    close_time_min: Optional[int] = None

    rating: Optional[float] = None
    review_count: Optional[int] = None
    popularity: Optional[int] = None

    price_vnd: Optional[float] = None
    dwell_min: Optional[int] = None

    tags: Optional[list[str]] = None
    image_url: Optional[str] = None


""" Hàm chuyển đổi từ các model khác sang ItinerarySpot"""
def place_lite_to_spot(p: PlaceLite) -> ItinerarySpot:
    # category: nếu chưa có, mặc định 'visit'
    category = p.category or "visit"

    lat = p.address.lat if p.address else 0.0
    lng = p.address.lng if p.address else 0.0

    open_min = time_str_to_min(p.openTime) if p.openTime else None
    close_min = time_str_to_min(p.closeTime) if p.closeTime else None

    return ItinerarySpot(
        id=p.id,
        name=p.name,
        category= "visit",
        lat=lat,
        lng=lng,
        open_time_min=open_min,
        close_time_min=close_min,
        rating=p.rating,
        review_count=p.reviewCount,
        popularity=p.popularity,
        price_vnd=float(p.priceVnd) if p.priceVnd is not None else None,
        dwell_min=p.dwell,  
        image_url=p.imageUrl,
        tags=p.tags,
    )

def food_place_to_spot(f: FoodPlace) -> ItinerarySpot:
    lat = f.address.lat if f.address else 0.0
    lng = f.address.lng if f.address else 0.0

    open_min = time_str_to_min(f.openTime) if f.openTime else None
    close_min = time_str_to_min(f.closeTime) if f.closeTime else None

    return ItinerarySpot(
        id=f.id,  
        name=f.name,
        category="eat",
        lat=lat,
        lng=lng,
        open_time_min=open_min,
        close_time_min=close_min,
        rating=f.rating,
        review_count=f.reviewCount,
        popularity=f.popularity,
        price_vnd=f.priceVNDPerPerson,  
        dwell_min=60,  
        image_url=f.imageUrl,
        tags=f.tags,
    )


def accommodation_to_spot(a: Accommodation) -> ItinerarySpot:
    lat = a.address.lat if a.address else 0.0
    lng = a.address.lng if a.address else 0.0

    return ItinerarySpot(
        id=a.id,  
        name=a.name or "",
        category="hotel",
        lat=lat,
        lng=lng,
        open_time_min=None,   
        close_time_min=None,
        rating=a.rating,
        popularity=a.popularity,
        price_vnd=a.priceVND,  
        dwell_min=None,    
        image_url=a.imageUrl,
        tags=a.tags,
    )
