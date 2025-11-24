"""In-memory implementation của IPlaceRepository"""
import logging
from typing import List, Optional, Dict
from app.application.interfaces.place_repository import IPlaceRepository
from app.domain.entities.PlaceLite import PlaceLite
from app.utils.normalize_text import normalize_text

logger = logging.getLogger(__name__) # Thiết lập logger cho module này

class InMemoryPlaceRepository(IPlaceRepository):
    """Dùng dict làm storage"""
    # Init method
    def __init__(self):
        """Khởi tạo storage và counter"""
        self._places: Dict[int, PlaceLite] = {}  # Storage
        self._next_id: int = 1         # ID counter     
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # public method
    async def find_by_keyword(self, keyword: str) -> List[PlaceLite]:
        """Tìm trong memory theo keyword"""
        return await self._find_by_keyword_memory(keyword)
    
    async def save(self, place: PlaceLite) -> int:
        """Lưu đối tượng hay dữ liệu địa điểm vào memory"""
        return await self._save_place_memory(place)
    
    async def update(self, place: PlaceLite) -> bool:
        """Cập nhật thông tin địa điểm trong memory"""
        return await self._update_place_memory(place)
    
    async def get_by_id(self, place_id: int) -> Optional[PlaceLite]:
        """Lấy thông tin địa điểm từ memory"""
        return await self._get_place_by_id_memory(place_id)
    
    async def delete_by_id(self, place_id: int) -> bool:
        """Xóa thông tin địa điểm khỏi memory"""
        return await self._delete_by_id_memory(place_id)
    
    async def get_all(self) -> List[PlaceLite]:
        """Lấy thông tin địa điểm tất cả places"""
        return list(self._places.values())
    
    async def count(self) -> int:
        """Đếm số lượng places"""
        return len(self._places)
    
    async def find_by_city(self, city: str) -> List[PlaceLite]:
        """Tìm theo thành phố"""
        return await self._find_by_city_memory(city)
    
    # Private methods
    
    async def _find_by_keyword_memory(self, keyword: str) -> List[PlaceLite]:
        """Tìm trong memory theo keyword"""
        if not keyword:
            return list(self._places.values())
        
        norm_kw = normalize_text(keyword).lower()
        results = [
            place for place in self._places.values()
            if norm_kw in normalize_text(place.name).lower()
        ]
        
        # Sort by popularity and rating
        results.sort(
            key=lambda p: (p.popularity, p.rating or 0),
            reverse=True
        )
        
        self.logger.debug(f"Found {len(results)} places for: {keyword}")
        return results
    
    async def _save_place_memory(self, place: PlaceLite) -> int:
        """lưu vào memory"""
        place_id = self._get_next_id()
        place.id = place_id
        self._places[place_id] = place
        self.logger.info(f"Saved place '{place.name}' with ID: {place_id}")
        return place_id
    
    async def _update_place_memory(self, place: PlaceLite) -> bool:
        """cập nhật trong memory"""
        if not place.id or place.id not in self._places:
            self.logger.warning(f"Place ID {place.id} not found")
            return False
        
        self._places[place.id] = place
        self.logger.info(f"Updated place ID {place.id}")
        return True
    
    async def _get_place_by_id_memory(self, place_id: int) -> Optional[PlaceLite]:
        """Lấy từ memory"""
        return self._places.get(place_id)
    
    async def _delete_by_id_memory(self, place_id: int) -> bool:
        """xóa khỏi memory"""
        if place_id in self._places:
            del self._places[place_id]
            self.logger.info(f"Deleted place ID {place_id}")
            return True
        return False
    
    async def _find_by_city_memory(self, city: str) -> List[PlaceLite]:
        """tìm theo thành phố trong memory"""
        norm_city = normalize_text(city).lower()
        return [
            place for place in self._places.values()
            if place.address and 
               normalize_text(place.address.city or "").lower() == norm_city
        ]
    
    
    # Hàm bổ sung
    def _get_next_id(self) -> int:
        """ Lấy ID tiếp theo và tăng counter"""
        current_id = self._next_id
        self._next_id += 1
        return current_id