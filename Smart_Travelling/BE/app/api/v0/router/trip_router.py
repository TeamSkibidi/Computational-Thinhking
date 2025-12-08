from fastapi import APIRouter
from typing import Dict

from app.api.schemas.itinerary_request import ItineraryRequest
from app.utils.response_format import success, error
from app.application.services import trip_service
router = APIRouter(
    prefix="/recommand",
    tags=["recommand"]
)

@router.post("/trip")
def Recommnad_trip(req: ItineraryRequest) -> Dict:

    try:
        data = trip_service.get_trip_itinerary(req)
        return success("Tạo lịch trình thành công", data=data)
    except ValueError as e:
        return error(str(e))

