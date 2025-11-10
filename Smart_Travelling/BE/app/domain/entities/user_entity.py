from datetime import datetime, timezone
from passlib.context import CryptContext
from User import User

# CryptContext là một thư viện con của passlib để quản lý thuật toán hash
# chọn "bcrypt" (an toàn, phổ biến và có salt ngẫu nhiên mỗi lần hash)
pwd_context = CryptContext(schemes=["bcrypt"])


# Class để nói đến các behavior liên qua đến người dùng
class UserEntity(User):
    
   
    def set_password(self, password: str):
        """
        Hash mật khẩu người dùng rồi lluw vào hashed_password
        sau đó cập nhật update_at để biết thời gian thay đổi gần nhất
        """
        self.hashed_password = pwd_context.hash(password)
        self.touch()

        
        
        
    def verify_password(self, password: str) -> bool:
        """
        Kiểm tra xem mật khẩu có khớp không
        cách hoạt động là Passlib.verify() tự đọc salt từ chuỗi hash đã lưu và hash lại input
        
        trả về:
        True: đúng mk
        False: sai mk
        """
        return pwd_context.verify(password, self.hashed_password)
    
    
    def change_password(self, old_password: str, new_password: str):
        """
        Đổi mật khẩu thì người dùng nhập đúng mật khẩu cũ nhằm người khác đổi mật khẩu
        Nếu old_password không đúng -> raise ValueError để tầng trên (service/router)
        bắt và trả về mã ỗi phù hợp
        """
        
        if not self.verify_password(old_password):
            raise ValueError("Mật khẩu cũ không đúng")
        self.set_password(new_password)
        
    def activate(self):
        """
        Kích hoạt tài khoản
        đổi is_active=True
        sau đó cập nhật update_at để lưu thời điểm đổi trạng thái
        
        vd:
        sau khi admin gỡ khóa tài khoản
        """
        
        self.is_active = True
        self.touch()

        
    def deactivate(self):
        """
        Khóa tài khoản.
        đổi is_active=False
        Cập nhật updated_at

        vd
        Người dùng yêu cầu tạm khóa.
        Hệ thống phát hiện vi phạm và admin khóa.
        """
        self.is_active = False
        self.touch()
        
    def touch(self):
        """
        ghi ngắn gọn hơn cập nhật thời gian thôi
        """
        self.updated_at = datetime.now(timezone.utc)
        
        
    