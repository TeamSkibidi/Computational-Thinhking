from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from domain.entities.nightstay import NightStay
from domain.entities.Address import Address


class StayPlan(BaseModel):
    guest_name: str
    start_date: Optional[date]
    end_date: Optional[date]
    stays: List[NightStay] 
    total_price: float

    def to_json(self) -> dict:
        """Chuyển object StayPlan → dict"""
        return {
            "guest_name": self.guest_name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat()if self.end_date else None,
            "stays": [stay.to_json() for stay in self.stays],
            "total_price": self.total_price
        }

    @classmethod
    def from_json(cls, data: dict) -> "StayPlan":
        stays_data = data.get("stays", [])
        stays = [NightStay.from_json(stay_data) for stay_data in stays_data]

        return cls(
            guest_name=data.get("guest_name"),
            start_date=date.fromisoformat(data.get("start_date")) if data.get("start_date") else None,
            end_date=date.fromisoformat(data.get("end_date")) if data.get("end_date") else None,
            stays=stays,
            total_price=data.get("total_price")
        )
