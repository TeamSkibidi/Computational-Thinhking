import logging
import os
import json 
import asyncio
from datetime import date
from typing import List
from domain.entities.nightstay import NightStay
from interface.NightStayRepository import INightStayRepository

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class NightStayRepository (INightStayRepository):
    def __init__ (self,  file_path: str = "data/nightstay.json") :
        self._nightStays : List[NightStay] = []
        self._file_path = file_path
# ---------------------------------------------------
#               Internal helper methods
# --------------------------------------------------
    async def _read_file(self) -> List[dict] :
        def sync_read():
            try:
                with open (self._file_path, "r", encoding="utf-8") as f :
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return []
        return await asyncio.to_thread(sync_read)
    
    async def _write_file (self, data: List[dict]) -> None :
        def sync_write ():
            with open (self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f , indent=4, ensure_ascii=False)
        await asyncio.to_thread(sync_write)

# --------------------------------------------------------------
#                   CRUD METHODS
#---------------------------------------------------------------

    async def save (self, nightstay: NightStay) -> None:
        data = await self._read_file()
        acc_dict = nightstay.to_json()
        data.append (acc_dict)
        await self._write_file(data)
        self._nightStays.append(nightstay)  # đồng bộ bộ nhớ
        logger.info(f"Đã lưu stayPlan '{nightstay.guest_name}' vào file.")

    async def update (self, nightstay: NightStay) -> bool:
        data = await self._read_file()
        for i, acc in enumerate (data):
            if acc.get("guest_name") == getattr (nightstay, "guest_name", None):
                data[i] = nightstay.to_json()
                await self._write_file(data)
                logger.info(f"Đã cập nhật stayPlan '{nightstay.guest_name}'.")
                return True 
            
        return False
    
    async def delete_by_guest_name (self, guestName : str)-> bool:
        data = await self._read_file()
        new_data = []
        for acc in data:
            if acc.get("guest_name") != guestName:
                new_data.append(acc)
        
        if len(new_data) == len(data):
            return False
        
        await self._write_file (new_data)
        logger.info(f"Đã xóa stayPlan '{guestName}'.")
        return True

    async def count (self) -> int:
        data = await self._read_file()
        return len(data)

# --------------------------------------------------
#                   GETTER
# --------------------------------------------------

    async def get_all (self) -> List[NightStay]:
        data = await self._read_file()
        result = []
        for acc in data:
           result.append(NightStay.from_json(acc))
        return result
# return [NightStay.from_json(acc) for acc in data]

    def get_guest_name (self) -> List[str] :
        return [acc.guest_name for acc in self._nightStays if acc.guest_name is not None]
    
    def get_check_in (self) -> List[date] :
        return [acc.check_in for acc in self._nightStays if acc.check_in is not None]
    
    def get_check_out (self) -> List[date]:
        return [acc.check_out for acc in self._nightStays if acc.check_out is not None]
    
    def get_priceVND (self) -> List[float]:
        return [acc.priceVND for acc in self._nightStays if acc.priceVND is not None]
    
    def get_num_guest (self) -> List[int]:
        return [acc.num_guest for acc in self._nightStays if acc.num_guest is not None]
    
    def get_type_guest (self) -> List[str]:
        return [acc.type_guest for acc in self._nightStays if acc.type_guest is not None]
    
    def get_summary (self) -> List[str]:
        return [acc.summary for acc in self._nightStays if acc.summary is not None]

# --------------------------------------------------------
#                       JSON 
# --------------------------------------------------------   
    def to_json (self) -> dict :
        nightStay_list = []
        for acc in self._nightStays :
            json_data = acc.to_json ()
            nightStay_list.append(json_data)

        result = {
             "night_stays" : nightStay_list
        }
        return result

    @classmethod
    def from_json(cls, data: dict) -> "NightStayRepository":
        repo = cls()
        for ns_data in data.get("night_stays", []):
            repo._nightStays.append(NightStay.from_json(ns_data))
        logger.info(f"Loaded {len(repo._nightStays)} stay plans from JSON.")
        return repo
    
# -----------------------------------------------
#               QUERY METHODS
# -----------------------------------------------
    async def find_by_price_range (self, min_price: float, max_price : float) -> List[NightStay]:
        data = await self._read_file()
        result = []
        
        for acc in data:
            price = acc.get("priceVND") or 0
            if price >=min_price and price <= max_price:
                result.append(NightStay.from_json(acc))
        
        return result
    
    async def find_by_keyword (self, keyword: str) -> List[NightStay]:
        data = await self._read_file()
        result = []

        for acc in data:
            summary = acc.get("summary", "").lower ()
            if keyword in summary:
                result.append(NightStay.from_json(acc))
        return result

    async def find_by_type_guest (self, typeGuest: str) -> List[NightStay]:
        data = await self._read_file()
        result = []

        for acc in data:
            type_Guest = acc.get("type_guest", "").lower()
            if typeGuest in type_Guest:
                result.append (NightStay.from_json(acc))
        return result
    
    async def find_by_guest_name (self, guestName: str) -> List[NightStay]:
        data = await self._read_file()
        result = []
        
        for acc in data:
            name = acc.get("guest_name", "").lower()
            if guestName in name:
                result.append (NightStay.from_json (acc))
        return result

    async def find_by_num_guest (self, min_num : int, max_num: int) -> List[NightStay]:
        data = await self._read_file()
        result = []

        for acc in data:
            num_guest= acc.get("num_guest")
            if num_guest <= max_num and num_guest >= min_num:
                result.append (NightStay.from_json(acc))
        return result