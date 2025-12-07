from datetime import date, time
from typing import List, Optional
from pydantic import BaseModel, Field


""" Cấu hình thời gian cho 1 khung trong ngày (buổi sáng, trưa, chiều, tối) """
class BlockTimeConfig(BaseModel):
    enabled: bool = True
    start: Optional[time] = None 
    end: Optional[time] = None

class ItineraryRequest(BaseModel):
    
    city: str
    start_date: date
    num_days : int = Field(..., ge=1, le=30)
    
     # 👉 thêm vào đây
    num_people: int = Field(1, ge=1, le=20)
    
    # Nếu FE gửi một mảng tags chung:
    tags: List[str] = []

    preferred_tags: List[str] = []
    avoid_tags: List[str] = []

    max_leg_distance_km: float = 5.0
    max_places_per_block: int = 3

    must_visit_place_ids: List[int] = []
    avoid_place_ids: List[int] = []

    """ Cấu hình thời gian cho các khung trong ngày """
    morning: BlockTimeConfig = BlockTimeConfig()
    lunch: BlockTimeConfig   = BlockTimeConfig()
    afternoon: BlockTimeConfig = BlockTimeConfig()
    dinner: BlockTimeConfig  = BlockTimeConfig()
    evening: BlockTimeConfig = BlockTimeConfig()
    
    user_id: Optional[int] = None
