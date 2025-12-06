from passlib.context import CryptContext
from typing import Dict, Optional, List
from app.adapters.repositories import user_repository      # chỉ import file thì nếu bên trong không có class thì dùng vâyj
from app.domain.entities.user_entity import UserEntity      #import tận class


#Đăng kí tài khoản
def register_user(data: Dict) -> bool:
    
    # Đăng ký tài khoản mới chỉ cần username + password.
    

    # Kiểm tra username trùng
    if user_repository.get_user_by_username(data["username"]):
        raise ValueError("Username đã tồn tại")

    # Tạo UserEntity — KHÔNG truyền toàn bộ data tránh lỗi
    entity = UserEntity(
        username=data["username"],
        email=None,              # vì không dùng email
        phone_number=None,       # vì không dùng phone
        hashed_password="",      # tạm để trống
        role="user",
        is_active=True,
        failed_attempts=0,
    )

    # Hash password
    entity.set_password(data["password"])

    # Convert sang dict để lưu DB
    user_dict = entity.model_dump()
   

    # Lưu DB
    return user_repository.create_user(user_dict)

#đăng nhập tài khoản
def login(username: str, password: str) -> Dict:
    """
    Đăng nhập người dùng bằng username + password.
    - Nếu sai -> tăng failed_attempts
    - Nếu sai >= 5 -> khóa tài khoản
    - Nếu đúng -> reset failed_attempts và cập nhật updated_at
    """

    # 1) Lấy user từ DB
    user_db = user_repository.get_user_by_username(username)
    if user_db is None:
        raise ValueError("Tài khoản không tồn tại.")

    # 2) Tạo Entity từ DB để xử lý logic
    entity = UserEntity(
        id=user_db["id"],
        username=user_db["username"],
        email=user_db.get("email"),
        phone_number=user_db.get("phone_number"),
        hashed_password=user_db["hashed_password"],
        role=user_db["role"],
        is_active=user_db["is_active"],
        failed_attempts=user_db["failed_attempts"],
        created_at=user_db.get("created_at"),
        updated_at=user_db.get("updated_at"),
    )

    # 3) Nếu tài khoản bị khóa -> không cho login
    if not entity.is_active:
        raise ValueError("Tài khoản đã bị khóa. Vui lòng liên hệ admin để mở khóa.")

    # 4) Xác thực mật khẩu 
    try:
        entity.verify_password(password)   # đúng thì return True, sai thì raise ValueError

    except ValueError as e:

        # Trường hợp bị khóa do sai quá 5 lần
        if not entity.is_active:
            user_repository.deactivate_user(entity.id)

        # Trường hợp chỉ sai < 5 lần → cập nhật failed_attempts
        else:
            user_repository.update_failed_attempts(entity.id, entity.failed_attempts)

        raise e   # ném lỗi lên router hoặc API

    # xuống tới đây tức là nhập đúng rồi

    # Reset số lần nhập sai
    user_repository.reset_failed_attempts(entity.id)

    # Trả dữ liệu an toàn
    return entity.to_safe_dict()


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    """
    USER - Đổi mật khẩu.
    Logic:
        - Lấy user từ DB
        - Tạo UserEntity để xử lý logic 
        - Nếu old sai → raise error trong Entity
        - Nếu đúng → set mật khẩu mới (hash)
        - Lưu hashed_password xuống DB
        - Cập nhật updated_at
    """

    # 1) Lấy user từ DB
    user_db = user_repository.get_user_by_id(user_id)
    if user_db is None:
        raise ValueError("User không tồn tại")

    # 2) Tạo entity từ DB
    entity = UserEntity(
        id=user_db["id"],
        username=user_db["username"],
        email=user_db.get("email"),
        phone_number=user_db.get("phone_number"),
        hashed_password=user_db["hashed_password"],
        role=user_db["role"],
        is_active=user_db["is_active"],
        failed_attempts=user_db["failed_attempts"],
        created_at=user_db.get("created_at"),
        updated_at=user_db.get("updated_at"),
    )

    # 3) Kiểm tra mật khẩu cũ + hash mật khẩu mới
    entity.change_password(old_password, new_password)

    # 4) Lưu hashed_password mới
    user_repository.update_user_password(entity.id, entity.hashed_password)

    # # 5) Reset số lần nhập sai về 0 (nếu có)
    # if entity.failed_attempts != 0:
    #     user_repository.reset_failed_attempts(entity.id)

    return True

#cập nhật thông tin người dùng (email, phone number)
def update_user_info(user_id: int, data: Dict) -> bool:
    """
    USER - Cập nhật thông tin cá nhân (email, phone_number).
    """

    updated_anything = False

    # check email trùng
    if "email" in data:
        new_email = data["email"]
        if new_email:
            existing = user_repository.get_user_by_email(new_email)
            if existing and existing["id"] != user_id:
                raise ValueError("Email đã tồn tại")

        # update email
        if user_repository.update_user_email(user_id, new_email):
            updated_anything = True

    # check số điện thoại trùng
    if "phone_number" in data:
        new_phone = data["phone_number"]

        # Nếu bạn muốn số điện thoại cũng unique:
        if new_phone:
            existing_phone = user_repository.get_user_by_phone(new_phone)
            if existing_phone and existing_phone["id"] != user_id:
                raise ValueError("Số điện thoại đã tồn tại")

        if user_repository.update_user_phone(user_id, new_phone):
            updated_anything = True

    return updated_anything

#lấy thông tin người dùng
def get_user_profile(user_id: int) -> Optional[Dict]:
    """
    USER - Lấy thông tin tài khoản của chính mình.
    Trả về dạng dict an toàn (không bao gồm hashed_password).
    """

    # 1. Lấy dữ liệu từ DB
    user_db = user_repository.get_user_by_id(user_id)
    if user_db is None:
        return None

    # 2. Tạo UserEntity từ dữ liệu DB
    entity = UserEntity(
        id=user_db["id"],
        username=user_db["username"],
        email=user_db.get("email"),
        phone_number=user_db.get("phone_number"),
        hashed_password=user_db["hashed_password"],
        role=user_db["role"],
        is_active=user_db["is_active"],
        failed_attempts=user_db["failed_attempts"],
        created_at=user_db.get("created_at"),
        updated_at=user_db.get("updated_at"),
    )

    # 3. Trả về thông tin an toàn (không trả hashed_password)
    return entity.to_safe_dict()




# PHẦN NÀY LÀ CÁC THAO TÁC CỦA ADMIN
#khóa tài khoản của user
def admin_deactivate_user(user_id: int) -> bool:
    """
    ADMIN – Khoá tài khoản người dùng (is_active = False).
    """

    user_db = user_repository.get_user_by_id(user_id)
    if user_db is None:
        raise ValueError("User không tồn tại")

    # Gọi hàm có khóa lại trong repository
    return user_repository.deactivate_user(user_id)


#mở khóa tài khoản người dùng
def admin_activate_user(user_id: int) -> bool:
    """
    ADMIN – Mở khoá tài khoản người dùng.
    Reset failed_attempts về 0.
    """

    user_db = user_repository.get_user_by_id(user_id)
    if user_db is None:
        raise ValueError("User không tồn tại")

    # 1) bật active = True
    result = user_repository.activate_user(user_id)
    
    # 2) reset số lần nhập sai
    user_repository.reset_failed_attempts(user_id)

    return result


# lấy ra danh sách của user
def admin_list_all_users() -> List[Dict]:
    """
    ADMIN – Xem danh sách user (không bao gồm admin).
    Xoá hashed_password trước khi trả ra API.
    """

    users = user_repository.get_all_users()

    # Xoá mật khẩu hash để an toàn
    for u in users:
        u.pop("hashed_password", None)

    return users

#xóa user
def admin_delete_user(user_id: int) -> bool:
    """
    ADMIN - Xoá user khỏi hệ thống.
    """

    user_db = user_repository.get_user_by_id(user_id)
    if user_db is None:
        raise ValueError("User không tồn tại")

    return user_repository.delete_user(user_id)


# Phần này llaf thao tác lấy tags
def get_user_tags(user_id: int):
    """
    USER - Lấy danh sách tags sở thích của user.
    """
    return user_repository.get_user_tags(user_id) or []


def update_user_tags(user_id: int, tags: List[str]) -> bool:
    """
    USER - Cập nhật danh sách tags sở thích.
    
    Tham số:
        user_id: ID người dùng
        tags: List các tag mới
    """
    if not isinstance(tags, list):
        raise ValueError("Tags phải là danh sách (list)")

    # Loại bỏ trùng lặp & trim khoảng trắng
    tags = list(set([t.strip() for t in tags if t and isinstance(t, str)]))

    return user_repository.update_user_tags(user_id, tags)