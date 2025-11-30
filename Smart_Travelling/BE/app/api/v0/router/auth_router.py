from fastapi import APIRouter
from typing import Dict

from app.application.services import user_service
from app.utils.response_format import success, error


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)



# ĐĂNG KÝ USER
@router.post("/register")
def register_user(data: Dict):
    try:
        user_service.register_user(data)
        return success("Đăng ký thành công. Vui lòng đăng nhập!")
    except ValueError as e:
        return error(str(e))


# ĐĂNG NHẬP USER
@router.post("/login")
def login(data: Dict):
    try:
        user = user_service.login(
            username=data["username"],
            password=data["password"]
        )
        return success("Đăng nhập thành công!", data=user)
    except ValueError as e:
        return error(str(e))
