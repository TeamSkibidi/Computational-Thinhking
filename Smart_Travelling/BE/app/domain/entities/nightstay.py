from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from .Address import Address

class NightStay(BaseModel): 
    guest_name: str
    num_guest : Optional[int] =  Field (None, ge = 0, description = "So luong khach") 


    def to_json (self) -> dict :
        return {
            "guest_name" : self.guest_name,
            "num_guest" : self.num_guest,
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
            num_guest=data.get("num_guest"),
        )

