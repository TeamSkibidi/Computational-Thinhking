# coding utf-8
from interface.AccommodationRepository import IAccommodationRepository
from domain.entities.accommodation import Accommodation
from domain.entities.Address import Address
from typing import List,Optional
import json
import asyncio
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class AccommodationRepository (IAccommodationRepository):
    
#------------------------INIT---------------------
    def __init__(self, file_path: str = "data/accommodation.json"):
        self._accommodations : List[Accommodation] = []
        self._file_path = file_path

# ---------------------------------------------------
#               Internal helper methods
# --------------------------------------------------
    async def _read_file (self) -> List[dict]:
        """Đọc toàn bộ dữ liệu từ file JSON."""
        def sync_read ():
            try:
                with open (self._file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return []
            
        return await asyncio.to_thread(sync_read)
    
    async def _write_file(self, data: List[dict]) -> None :
        """Ghi toàn bộ dữ liệu accommodation vào file JSON."""
        def sync_write ():
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f , indent= 4, ensure_ascii=False)
        await asyncio.to_thread(sync_write)

# --------------------------------------------------------------
#                   CRUD METHODS
#---------------------------------------------------------------

    async def save (self, accommodation : Accommodation) -> None :
        """Thêm accommodation mới vào file."""
        data = await self._read_file()
        acc_dict = accommodation.to_json()
        data.append(acc_dict)
        await self._write_file(data)
        logger.info(f"Đã lưu accommodation '{accommodation.name}' vào file.")

    
    async def update (self, accommodation : Accommodation) -> bool:
        """Cập nhật accommodation theo tên."""
        data = await self._read_file()
        for i, acc in enumerate (data):
            if acc.get("name") == getattr(accommodation, "name", None):
                data[i] = accommodation.to_json()
                await self._write_file(data)
                logger.info(f"Đã cập nhật accommodation '{accommodation.name}'.")
                return True
        return False
    
   
    async def delete_by_name(self, accommodation_name: str) -> bool:
        """Xóa accommodation theo tên."""
        data = await self._read_file()
        new_data = []
        for acc in data:
            if acc.get("name") != accommodation_name:
                new_data.append(acc)

        if len(new_data) == len(data):
        # Không có bản ghi nào bị xóa → ID không tồn tại
            return False

        await self._write_file(new_data)
        logger.info(f"Đã xóa accommodation '{accommodation_name}'.")
        return True


    async def count (self) -> int:
        data = await self._read_file()
        return len (data)

# -----------------------------------------------
#               QUERY METHODS
# -----------------------------------------------

    async def find_by_keyword(self, keyword: str) -> List[Accommodation]:
        """Tìm theo từ khóa trong tên hoặc mô tả.""" 
        data = await self._read_file()
        keyword = keyword.lower ()
        result = []
        for acc in data :
            name = acc.get("name", "").lower()
            summary = acc.get("summary", "").lower()

            if keyword in name or keyword in summary:
                result.append(Accommodation.from_json(acc))

        return result
    
    async def find_by_city (self, city: str) -> List[Accommodation] :
        data = await self._read_file()
        city = city.lower()

        result = []
        for acc in data:
            address_data = acc.get("address")
            if not address_data:
                continue

            acc_city = address_data.get("city", "").lower()
            if acc_city == city:
                result.append(Accommodation.from_json(acc))

        return result

    async def find_by_rating (self, min_rating : float) -> List[Accommodation]:
        data = await self._read_file()
        result = []
        
        for acc in data:
            rating = acc.get("rating") or 0
            if rating >= min_rating:
                result.append(Accommodation.from_json(acc))

        return result
        
    async def find_by_price_range (self, min_price: float, max_price: float) -> List[Accommodation]:
        data = await self._read_file()
        result = []

        for acc in data:   
            price = acc.get("priceVND") or 0
            if price >= min_price and price <= max_price:
                result.append (Accommodation.from_json(acc))

        return result
# --------------------------------------------------
#                   GETTER
# --------------------------------------------------

    async def get_all(self) -> List[Accommodation]:
        """Lấy toàn bộ danh sách accommodation từ file."""
        data = await self._read_file()
        return [Accommodation.from_json(acc) for acc in data]
    
    def get_name (self) -> List[str]:
        names = []
        for acc in self._accommodations:
            if acc.name :
                names.append (acc.name)
        return names
    
    def get_rating (self) -> List[float] :
        return [acc.rating for acc in self._accommodations if acc.rating is not None]
    
    def get_popularity (self) -> List[int] :
        return [acc.popularity for acc in self._accommodations if acc.popularity is not None]
    
    def get_reviewCount (self) -> List[int] :
        return [acc.reviewCount for acc in self._accommodations__ if acc.reviewCount is not None]
    

# --------------------------------------------------------
#                       JSON 
# --------------------------------------------------------

    def to_json (self) -> dict :
        accommodation_list = []
        for acc in self._accommodations:
            json_data = acc.to_json ()
            accommodation_list.append(json_data)
        
        result = {
            "accommodations" : accommodation_list
        }
        return result
    

    @classmethod
    def from_json (cls, data: dict) -> "AccommodationRepository" :
        repo = cls()
        for acc_data in data.get("accommodations", []):
            repo.add(Accommodation.from_json(acc_data))
        logging.info (f"Loaded {len(repo._accommodations)} accommodations from JSON")
        return repo