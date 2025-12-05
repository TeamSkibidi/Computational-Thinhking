from fastapi import APIRouter
from typing import Dict, List

from app.application.services import tag_service
from app.utils.response_format import success, error

router = APIRouter(
    prefix="/tags",
    tags=["Tags"]
)


@router.get("/{tag}")
def get_all_tag(tag: List[str]):
    tags = tag_service.get_all_places_by_tag(tag)
    if tags is None:
        return error("Tag không có tồn tại")
    return success("Lấy danh sách địa điểm theo tag thành công!", data=tags)


