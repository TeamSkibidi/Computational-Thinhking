from datetime import Date
from typing import List, Dict
from pydantic import BaseModel, Field

""" Thông tin của 1 địa điểm tham quan trong 1 buổi"""
class BlockItemResponse(BaseModel):
    order: int = Field(..., example=1)
    type: str = Field(..., example="visit")
    name: str = Field(..., example="Nhà thờ Lớn Hà Nội")
    start: str = Field(..., example="07:30")  # HH:MM
    end: str = Field(..., example="09:00")    # HH:MM
    distance_from_prev_km: float = Field(..., example=3.2)
    travel_from_prev_min: int = Field(..., example=40)
    dwell_min: int = Field(..., example=90)
    image_url: str | None = Field(None, example="https://cdn.../place.jpg")
    price_vnd: int | None = Field(None, example=50000)

"""Tổng hợp chi phí trong ngày không bao gồm ăn uống và di chuyển nha (chỉ tính tham quan với khách sạn thôi    )"""
class CostSummaryResponse(BaseModel):
    total_attraction_cost_vnd: int = Field(..., example=150000)
    total_accommodation_cost_vnd: int = Field(..., example=120000)
    total_trip_cost_vnd: int = Field(..., example=270000)



""" Lịch trình cho 1 ngày gồm trưa chiều tối"""
class DayItineraryResponse(BaseModel):

    city: str = Field(..., example="Hanoi")
    date: Date = Field(..., example="2025-12-20")

    """ Ứng với mỗi buổi sẽ có 1 danh sách các hoạt động cho nhaaa"""
    blocks: Dict[str, List[BlockItemResponse]] = Field(
        ...,
        example={
            "morning": [],
            "lunch": [],
            "afternoon": [],
            "dinner": [],   
            "evening": [],
        },
    )
    cost_summary: CostSummaryResponse
