from datetime import datetime, timezone
from passlib.context import CryptContext
from User import User

# CryptContext là một thư viện con của passlib để quản lý thuật toán hash
# chọn "bcrypt" (an toàn, phổ biến và có salt ngẫu nhiên mỗi lần hash)
pwd_context = CryptContext(schemes=["bcrypt"])


# Class để nói đến các behavior liên qua đến người dùng
class UserEntity(User):
    
    """
    Hash mật khẩu người dùng rồi lluw vào hashed_password
    sau đó cập nhật update_at để biết thời gian thay đổi gần nhất
    
    """
    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)
        self.updated_at = datetime.now(timezone.utc)
        
    