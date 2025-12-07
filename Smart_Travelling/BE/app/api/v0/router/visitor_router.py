# app/api/v0/routes/visitor_router.py
from fastapi import APIRouter
from typing import Dict, List, Set

from app.application.services import visitor_service
from app.utils.response_format import success, error

router = APIRouter(
    prefix="/visitor",
    tags=["Visitor"]
)


# GỢI Ý ĐỊA ĐIỂM THAM QUAN THEO THÀNH PHỐ
@router.post("/recommend")
def recommend_places(data: Dict):
    """
    Body gửi lên (JSON):

    {
      "city": "Ho Chi Minh",
      "seen_ids": [1, 2, 3],   # optional – danh sách id đã gợi ý trước đó
      "k": 5                   # optional – số lượng cần gợi ý, mặc định 5
    }
    """

    try:
        # Lấy city (bắt buộc)
        city = data["city"]

        # seen_ids: danh sách id đã xem (optional)
        raw_seen: List[int] = data.get("seen_ids", []) or []
        seen_ids: Set[int] = set(raw_seen)

        # k: số lượng địa điểm muốn gợi ý (optional, default = 5)
        
        k = 5

        # Gọi service để random địa điểm KHÔNG LẶP
        places, new_seen_ids = visitor_service.recommend_places_by_city(
            city=city,
            seen_ids=seen_ids,
            k=k,
        )

        # Convert PlaceLite (BaseModel) -> dict để trả JSON
        places_data = [p.model_dump() for p in places]

        return success(
            "Gợi ý địa điểm tham quan thành công!",
            data={
                "city": city,
                "places": places_data,
                "seen_ids": list(new_seen_ids),  # FE lưu lại để lần sau gửi lên
            },
        )

    except KeyError:
        # thiếu city trong body
        return error("Thiếu trường 'city' trong request body")

    except ValueError as e:
        # lỗi logic do mình raise ValueError trong service (nếu có)
        return error(str(e))

    except Exception as e:
        # lỗi không mong muốn
        # (khi làm thật có thể log ra, ở đây trả message chung)
        return error("Có lỗi xảy ra khi gợi ý địa điểm")
