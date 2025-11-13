import logging
import json
import asyncio
import os
from typing import List
from datetime import date
from domain.entities.stayplan import StayPlan
from interface.StayPlanRepository import IStayPlanRepository

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class StayPlanRepository(IStayPlanRepository):
    def __init__(self, file_path: str = "data/stayplan.json"):
        self._plans: List[StayPlan] = []
        self._file_path = file_path

# ---------------------------------------------------
#               Internal helper methods
# --------------------------------------------------
    async def _read_file (self) ->List[dict]:
        def sync_read ():
            try:
                with open (self._file_path, "r", encoding= "utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return []
    
    async def _write_file (self, data: List[dict]) -> None:
        def sync_write ():
            with open (self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f , indent=4, ensure_ascii=False)
        await asyncio.to_thread(sync_write)

# --------------------------------------------------
#                   GETTER
# --------------------------------------------------

    async def get_all(self) -> List[StayPlan]:
        data = await self._read_file()
        return [StayPlan.from_json(acc) for acc in data]
    
    def get_guest_name(self) -> List[str]:
        return [plan.guest_name for plan in self._plans]

    def get_start_date(self) -> List[date]:
        return [plan.start_date for plan in self._plans]

    def get_end_date(self) -> List[date]:
        return [plan.end_date for plan in self._plans]

    def get_total_price(self) -> List[float]:
        return [plan.total_price for plan in self._plans]

    def get_num_night_stay(self) -> List[int]:
        return [len(plan.stays) for plan in self._plans]
# -----------------------------------------------
#               QUERY METHODS
# -----------------------------------------------
 
    async def find_by_keyword(self, keyword : str) -> List[StayPlan]:
        data = await self._read_file()
        result = []
        for acc in data:
            summary =  acc.get("summary", "").lower()
            if keyword in summary:
                result.append(StayPlan.from_json(acc))
        return result
 
    async def find_by_price_range (self, min_price : float , max_price : float) -> List[StayPlan]:
        data = await self._read_file()
        result = []

        for acc in data:
            price = acc.get("price") or 0
            if price <= max_price and price >= min_price:
                result.append(StayPlan.from_json(acc))
        return result
 
    async def find_by_city (self, city : str) -> List[StayPlan]:
        pass

# --------------------------------------------------------------
#                   CRUD METHODS
#--------------------------------------------------------------- 
    async def save (self, stay_plan : StayPlan) -> None :
        data = await self._read_file()
        acc_dict = stay_plan.to_json()
        data.append(acc_dict)
        await self._write_file(data)
        self._plans.append(stay_plan)
        logger.info(f"Đã lưu stayPlan '{stay_plan.guest_name}' vào file.")

    async def update (self, stay_plan : StayPlan) -> bool:
        data = await self._read_file()
        for i, acc in enumerate(data):
            if acc.get("guest_name") == getattr (stay_plan, "guest_name", None):
                data[i] = stay_plan.to_json()
                await self._write_file(data)
                logger.info(f"Đã cập nhật stayPlan '{stay_plan.guest_name}'.")
                return True
        
        return False
 
    async def delete_by_guest_name(self, guestName: str) -> bool:
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

# --------------------------------------------------------
#                       JSON 
# --------------------------------------------------------

    def to_json(self) -> dict:
        return {"stay_plans": [plan.to_json() for plan in self._plans]}

    @classmethod
    def from_json(cls, data: dict) -> "StayPlanRepository":
        repo = cls()
        for plan_data in data.get("stay_plans", []):
            repo.add(StayPlan.from_json(plan_data))
        logging.info(f"Loaded {len(repo._plans)} stay plans from JSON.")

        return repo
