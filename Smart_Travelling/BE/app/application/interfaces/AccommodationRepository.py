"""Accommodation repository interface - Clean Architecture"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entites.accommodation import Accommodation


class IAccommodationRepository(ABC):
# -----------------------------------------
#               GETTER
# -----------------------------------------  
     
    @abstractmethod
    async def get_all(self) -> List[Accommodation]:
        """Lấy tất cả accommodations"""
        pass 

    @abstractmethod
    def get_name(self) -> List[Accommodation]:
        pass

    @abstractmethod
    def get_rating(self) -> List[Accommodation]:
        pass

    @abstractmethod
    def get_popularity(self) -> List[Accommodation]:
        pass 

    @abstractmethod
    def get_reviewCount(self) -> List[Accommodation]:
        pass


# --------------------------------------------
#               QUERY METHODS
# --------------------------------------------

    # tìm ký tự từ trong summary và trả về List[Accommodation] chứa các keyword đó 
    @abstractmethod
    async def find_by_keyword(self, keyword: str) -> List[Accommodation]:
        """Tìm accommodations theo từ khóa"""
        pass


    @abstractmethod
    async def delete_by_name(self, accommodation_id: int) -> bool:
        """Xóa accommodation theo Name"""
        pass


    @abstractmethod
    async def count(self) -> int:
        """Đếm tổng số accommodations"""
        pass

    @abstractmethod
    async def find_by_city(self, city: str) -> List[Accommodation]:
        """Tìm accommodations theo thành phố"""
        pass

    @abstractmethod
    async def find_by_rating(self, min_rating: float) -> List[Accommodation]:
        """Tìm accommodations có rating >= min_rating"""
        pass

    @abstractmethod
    async def find_by_price_range(self, min_price: float, max_price: float) -> List[Accommodation]:
        """Tìm accommodations trong khoảng giá"""
        pass


#---------------------------
# CRUD
# ---------------------------

    # Dùng để thêm một đối tượng mới vào hàm 
    # Cần thêm dữ liệu của Khôi vào vì chưa có sẵn 
    # -> Dùng hàm này 
    @abstractmethod
    async def save(self, accommodation: Accommodation) -> None: 
        pass

    # Dùng để ghi đè lên một đối tượng đã có sẵn trong file 
    # Ví dụ đã có dữ liệu name = Khôi -> Cần cập nhật thông tin mới 
    # -> Dùng hàm này
    @abstractmethod
    async def update(self, accommodation: Accommodation) -> bool:
        """Cập nhật accommodation, trả về success status"""
        pass


    def to_json(self) -> dict :
        pass

    @classmethod
    def from_json (cls, data : dict) -> Accommodation :
        pass
