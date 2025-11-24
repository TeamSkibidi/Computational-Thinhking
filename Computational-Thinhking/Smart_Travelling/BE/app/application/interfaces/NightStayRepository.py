#coding utf-8
from typing import List
from datetime import date
from domain.entities.nightstay import NightStay
from abc import ABC, abstractmethod

class INightStayRepository(ABC):
# --------------------------------------------------
#                   GETTER
# --------------------------------------------------
    @abstractmethod
    def get_all (self) -> List[NightStay] :
        pass
    

    @abstractmethod
    def get_guest_name (self) -> List[str] :
        pass

    @abstractmethod
    def get_check_in (self) -> List[date] :
        pass

    @abstractmethod
    def get_check_out (self) -> List[date]:
        pass

    @abstractmethod
    def get_priceVND (self) -> List[float]:
        pass 

    @abstractmethod
    def get_num_guest (self) -> List[int]:
        pass

    @abstractmethod
    def get_type_guest (self) -> List[str]:
        pass

    @abstractmethod 
    def get_summary (self) -> List[str]:
        pass
    
# -----------------------------------------------
#               QUERY METHODS
# -----------------------------------------------

    @abstractmethod 
    async def find_by_price_range (self, min_price: float, max_price : float) -> List[NightStay]:
        pass

    @abstractmethod 
    async def find_by_type_guest (self, typeGuest: str) -> List[NightStay]:
        pass

    @abstractmethod 
    async def find_by_guest_name (self, guestName: str) -> List[NightStay]:
        pass

    @abstractmethod 
    async def find_by_num_guest (self, numGuest : int) -> List[NightStay]:
        pass

    @abstractmethod
# tìm các từ khoá xuất hiện ở trong summary 
    async def find_by_keyword (self, keyword: str) -> List[NightStay]: 
        pass

# --------------------------------------------------------------
#                   CRUD METHODS
#---------------------------------------------------------------
    
    # Dùng để thêm một đối tượng mới vào hàm 
    # Cần thêm dữ liệu của Khôi vào vì chưa có sẵn 
    # -> Dùng hàm này
    @abstractmethod 
    async def save (self, nightStay : NightStay) -> None:
        pass

    # Dùng để ghi đè lên một đối tượng đã có sẵn trong file 
    # Ví dụ đã có dữ liệu name = Khôi -> Cần cập nhật thông tin mới 
    # -> Dùng hàm này
    async def update (self, nightStay : NightStay)-> bool:
        pass

    async def delete_by_guest_name (self, guest_name: str) -> bool:
        pass

    async def count (self) -> int:
        pass
    
    async def delete_by_guest_name (self, guestName : str)-> bool:
        pass

# --------------------------------------------------------
#                       JSON 
# --------------------------------------------------------
    def to_json (self) -> dict:
        pass

    @classmethod 
    def from_json (cls, data: dict) -> "NightStay":
        pass

