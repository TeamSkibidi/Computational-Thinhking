from abc import ABC, abstractmethod
from typing import List
from datetime import date
from domain.etiities.data.stayplan import StayPlan
from domain.etiities.data.nightstay import NightStay

class IStayPlanRepository(ABC):

# --------------------------------------------------
#                   GETTER
# --------------------------------------------------
    @abstractmethod
    def get_all(self) -> List[StayPlan]:
        pass

    @abstractmethod
    def get_guest_name(self) -> List[str]:
        pass

    @abstractmethod
    def get_start_date(self) -> List[date]:
        pass

    @abstractmethod
    def get_end_date(self) -> List[date]:
        pass

    @abstractmethod
    def get_total_price(self) -> List[float]:
        pass

    @abstractmethod
    def get_num_night_stay(self) -> List[int]:
        pass
# -----------------------------------------------
#               QUERY METHODS
# -----------------------------------------------

    @abstractmethod 
    async def find_by_keyword(self, keyword : str) -> List[StayPlan]:
        pass

    @abstractmethod 
    async def find_by_price_range (self, min_price : float , max_price : float) -> List[StayPlan]:
        pass

    @abstractmethod 
    async def find_by_city (self, city : str) -> List[StayPlan]:
        pass

# --------------------------------------------------------------
#                   CRUD METHODS
#---------------------------------------------------------------

    # Dùng để thêm một đối tượng mới vào hàm 
    # Cần thêm dữ liệu của Khôi vào vì chưa có sẵn 
    # -> Dùng hàm này
    @abstractmethod 
    async def save (self, stay_plan : NightStay) -> None :
        pass

    # Dùng để ghi đè lên một đối tượng đã có sẵn trong file 
    # Ví dụ đã có dữ liệu name = Khôi -> Cần cập nhật thông tin mới 
    # -> Dùng hàm này
    @abstractmethod 
    async def update (self, stay_plan : NightStay) -> bool:
        pass

    @abstractmethod 
    async def delete_by_guest_name(self, guestName: str) -> bool:
        pass

    @abstractmethod
    async def count (self) -> int:
        pass

# --------------------------------------------------------
#                       JSON 
# --------------------------------------------------------

    @classmethod
    def from_json(cls, data: dict) -> "StayPlan":
        pass

    def to_json (self) -> dict:
        pass



    
