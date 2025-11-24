from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from domain.entities.Address import Address

class NightStay(BaseModel): 
    guest_name: str
    summary : str
    check_in : Optional[date] 
    check_out : Optional[date]
    priceVND : Optional[float]  # gia 1 dem
    num_guest : Optional[int] =  Field (None, ge = 0, description = "So luong khach") 
    type_guest : str = Field (default = "", description = "Nhom doi tuong")


    def to_json (self) -> dict :
        return {
            "guest_name" : self.guest_name,
            "check_in" : self.check_in.isoformat() if self.check_in else None,
            "check_out" : self.check_out.isoformat () if self.check_out else None,
            "priceVND" : self.priceVND,
            "num_guest" : self.num_guest,
            "type_guest" : self.type_guest
        }
    @classmethod
    def from_json (cls, data : dict ) ->  "NightStay" :
        def parse_date(value):
            if isinstance(value, date):
                return value
            if isinstance(value, str) and value :
                return date.fromisoformat (value)
            return None

        return cls(
            guest_name=data.get("guest_name", ""),
            check_in=parse_date(data.get("check_in")),
            check_out=parse_date(data.get("check_out")),
            priceVND=data.get("priceVND"),
            num_guest=data.get("num_guest"),
            type_guest=data.get("type_guest", "")
        )

