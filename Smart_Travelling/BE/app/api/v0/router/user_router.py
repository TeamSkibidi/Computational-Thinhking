from fastapi import APIRouter
from typing import Dict

from app.application.services import user_service
from app.utils.response_format import success, error


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# LẤY PROFILE
@router.get("/{user_id}")
def get_profile(user_id: int):
    user = user_service.get_user_profile(user_id)
    if user is None:
        return error("User không tồn tại")

    return success("Lấy thông tin user thành công!", data=user)



# CẬP NHẬT THÔNG TIN USER
@router.post("/update-info")
def update_info(data: Dict):
    try:
        user_service.update_user_info(
            user_id=data["user_id"],
            data=data
        )
        return success("Cập nhật thông tin thành công!")
    except ValueError as e:
        return error(str(e))



# ĐỔI MẬT KHẨU
@router.post("/change-password")
def change_password(data: Dict):
    try:
        user_service.change_password(
            user_id=data["user_id"],
            old_password=data["old_password"],
            new_password=data["new_password"]
        )
        return success("Đổi mật khẩu thành công!")
    except ValueError as e:
        return error(str(e))
    
# các thao tác với tags
# CẬP NHẬT TAGS
@router.post("/{user_id}/tags")
def update_user_tags(user_id: int, data: Dict):
    """
    Cập nhật danh sách tags sở thích.
    
    Body:
    {
        "tags": ["Du lịch", "Ẩm thực", "Thiên nhiên"]
    }
    """
    try:
        tags = data.get("tags", [])
        user_service.update_user_tags(user_id, tags)
        return success("Cập nhật tags thành công!")
    except ValueError as e:
        return error(str(e))