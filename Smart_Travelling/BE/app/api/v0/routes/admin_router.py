from fastapi import APIRouter
from app.application.services import user_service
from app.utils.response_format import success, error


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


# ADMIN – XEM DANH SÁCH USER
@router.get("/users")
def list_users():
    users = user_service.admin_list_all_users()
    return success("Lấy danh sách người dùng thành công!", data=users)



# ADMIN – KHÓA USER
@router.put("/users/deactivate/{user_id}")
def deactivate_user(user_id: int):
    try:
        user_service.admin_deactivate_user(user_id)
        return success("Đã khóa tài khoản user")
    except ValueError as e:
        return error(str(e))



# ADMIN – MỞ KHÓA USER
@router.put("/users/activate/{user_id}")
def activate_user(user_id: int):
    try:
        user_service.admin_activate_user(user_id)
        return success("Đã mở khóa tài khoản user")
    except ValueError as e:
        return error(str(e))



# ADMIN – XOÁ USER
@router.delete("/users/delete/{user_id}")
def delete_user(user_id: int):
    try:
        user_service.admin_delete_user(user_id)
        return success("Xóa người dùng thành công")
    except ValueError as e:
        return error(str(e))
