from fastapi import APIRouter
from typing import Dict, List

from app.api.schemas.itinerary_request import ItineraryRequest
from app.utils.response_format import success, error
from app.application.services import trip_service, trip_history_file_service
router = APIRouter(
    prefix="/recommand",
    tags=["recommand"]
)

@router.post("/trip")
def Recommnad_trip(req: ItineraryRequest) -> Dict:
    print("Received itinerary request:", req)
    print(f"User ID from request: {req.user_id}")

    try:
        data = trip_service.get_trip_itinerary(req)
        
        # ===== TÍNH TOTAL COST TỪ trip_data =====
        days = data.get("days", [])
        total_cost = 0

        # Nếu mỗi day có cost_summary.total_trip_cost_vnd thì cộng lại
        for day in days:
            cost_summary = day.get("cost_summary") or {}
            if "total_trip_cost_vnd" in cost_summary:
                total_cost += cost_summary["total_trip_cost_vnd"]
            elif "total_attraction_cost_vnd" in cost_summary:
                total_cost += cost_summary["total_attraction_cost_vnd"]

        # ===== TẠO LIST PLACES ĐƠN GIẢN ĐỂ HIỂN THỊ LỊCH SỬ =====
        summary_places: List[Dict[str, Any]] = []
        for day in days:
            date = day.get("date")
            for block_name, block_places in (day.get("blocks") or {}).items():
                for p in block_places:
                    summary_places.append({
                        "name": p.get("name"),
                        "type": p.get("type"),
                        "day": date,
                        "block": block_name,
                        "price_vnd": p.get("price_vnd", 0),
                        "image_url": p.get("image_url")
                    })
        
        # ✅ Lưu vào file nếu FE gửi user_id
        if req.user_id:
            trip_history_file_service.save_trip_to_file(
                user_id=req.user_id,
                trip_data={
                    "city": req.city,
                    "start_date": req.start_date.isoformat(),
                    "num_days": req.num_days,
                    "num_people": req.num_people,
                    "total_cost": total_cost,
                    "places": summary_places,
                    "tags": getattr(req, "preferred_tags", []) or [],
                    "trip_data": data
                }
            )
            print(f"✅ Saved trip history for user {req.user_id}")
        
        
        
        return success("Tạo lịch trình thành công", data=data)
    except ValueError as e:
        return error(str(e))
    
@router.get("/history/{user_id}")
def get_trip_history(user_id: int) -> Dict:
    """Lấy lịch sử trip của user gom nhóm theo ngày"""
    if not user_id:
        return error("Vui lòng cung cấp user_id", code=400)
    
    trips = trip_history_file_service.load_trip_history(user_id)
    
    trips_by_date = {}
    for trip in trips:
        created_at = trip.get("created_at", "")
        date_key = created_at[:10]
        
        if date_key not in trips_by_date:
            trips_by_date[date_key] = []
        
        trips_by_date[date_key].append({
            "id": trip.get("id"),
            "city": trip.get("city"),
            "num_days": trip.get("num_days"),
            "num_people": trip.get("num_people"),
            "total_cost": trip.get("total_cost"),
            "created_at": trip.get("created_at"),
        })
    
    return success(
        "Lấy lịch sử thành công",
        data={
            "trips_by_date": trips_by_date,
            "total_trips": len(trips)
        }
    )
    
@router.get("/history/{user_id}/{trip_id}")
def get_trip_detail(user_id: int, trip_id: int) -> Dict:
    """Lấy chi tiết 1 trip (KHÔNG đổi id nữa)"""
    trip = trip_history_file_service.get_trip_detail(user_id, trip_id)

    if not trip:
        return error("Không tìm thấy trip", 404)

    # Không cần update_access_time nữa
    # trip_history_file_service.update_trip_access_time(user_id, trip_id)

    return success("Lấy chi tiết trip thành công", trip)

@router.delete("/history/{user_id}/{trip_id}")
def delete_trip(trip_id: int, user_id: int) -> Dict:
    """Xóa 1 trip"""
    if not user_id:
        return error("Vui lòng cung cấp user_id", code=400)
    
    deleted = trip_history_file_service.delete_trip(user_id, trip_id)
    
    if not deleted:
        return error("Không tìm thấy trip", code=404)
    
    return success("Xóa trip thành công")

@router.delete("/history/{user_id}")
def delete_all_trips(user_id: int) -> Dict:
    """Xóa toàn bộ lịch sử trip"""
    if not user_id:
        return error("Vui lòng cung cấp user_id", code=400)
    
    trip_history_file_service.delete_all_trips(user_id)
    
    return success("Xóa toàn bộ lịch sử thành công")

