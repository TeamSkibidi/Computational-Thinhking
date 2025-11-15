from passlib.context import CryptContext
from typing import Dict, Optional, List
from app.adapters.repositories import user_repository
from app.domain.entities.user_entity import UserEntity

# chọn thuật toán bycypt để hash mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"])


#Đăng kí tài khoản
def register_user(data: Dict) -> int:
    
    # Đăng ký tài khoản mới chỉ cần username + password.
    

    # 1. Kiểm tra username trùng
    if user_repository.get_user_by_username(data["username"]):
        raise ValueError("Username đã tồn tại")

    # 2. Tạo UserEntity — KHÔNG truyền toàn bộ data tránh lỗi
    entity = UserEntity(
        username=data["username"],
        email=None,              # vì không dùng email
        phone_number=None,       # vì không dùng phone
        hashed_password="",      # tạm để trống
        role="user",
        is_active=True,
        failed_attempts=0,
    )

    # 3. Hash password
    entity.set_password(data["password"])

    # 4. Convert sang dict để lưu DB
    user_dict = entity.model_dump()
   

    # 5. Lưu DB
    return user_repository.create_user(user_dict)
