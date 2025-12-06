# app/api/schemas/event_request.py
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class EventRecommendationRequest(BaseModel):
    city: str = Field(..., example="Hanoi")
    target_date: date = Field(..., example="2025-02-01")
    session: Optional[str] = Field(None, example="morning")
    lat: Optional[float] = Field(None, ge=-90, le=90, example=21.0278)
    lng: Optional[float] = Field(None, ge=-180, le=180, example=105.8342)
    max_distance_km: Optional[float] = Field(None, gt=0, example=10.0)


class EventListRequest(BaseModel):
    city: str = Field(..., example="Hanoi")
    target_date: date = Field(..., example="2025-02-01")
    session: Optional[str] = Field(None, example="morning")

    sort: Optional[str] = Field(
        None,
        description="price_asc | price_desc | popularity_desc",
        example="price_asc",
    )


class EventSearchByNameRequest(BaseModel):
    keyword: str = Field(
        ...,
        min_length=1,
        description="Tên lễ hội cần tìm",
        example="Lễ hội pháo hoa",
    )
    limit: int = Field(5, ge=1, le=20, example=5)
