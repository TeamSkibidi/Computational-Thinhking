"""Place repository interface - Clean Architecture"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.PlaceLite import PlaceLite


class IPlaceRepository(ABC):
    """
    Repository interface cho Place entity.
    
    Chỉ định nghĩa PUBLIC methods mà các implementation phải có.
    Các private methods (_xxx) là internal của từng implementation.
    """

    @abstractmethod
    async def find_by_keyword(self, keyword: str) -> List[PlaceLite]:
        """Tìm places theo keyword"""
        pass

    @abstractmethod
    async def save(self, place: PlaceLite) -> int:
        """Lưu place mới, trả về ID"""
        pass

    @abstractmethod
    async def update(self, place: PlaceLite) -> bool:
        """Cập nhật place, trả về success status"""
        pass

    @abstractmethod
    async def get_by_id(self, place_id: int) -> Optional[PlaceLite]:
        """Lấy place theo ID"""
        pass

    @abstractmethod
    async def delete_by_id(self, place_id: int) -> bool:
        """Xóa place theo ID"""
        pass

    @abstractmethod
    async def get_all(self) -> List[PlaceLite]:
        """Lấy tất cả places"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Đếm số lượng places"""
        pass

    @abstractmethod
    async def find_by_city(self, city: str) -> List[PlaceLite]:
        """Tìm places theo thành phố"""
        pass

        
