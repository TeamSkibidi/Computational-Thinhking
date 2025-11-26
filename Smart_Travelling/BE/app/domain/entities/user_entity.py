from datetime import datetime, timezone
from passlib.context import CryptContext
from app.domain.entities.User import User
from typing import ClassVar

# CryptContext là một thư viện con của passlib để quản lý thuật toán hash
# chọn "bcrypt" (an toàn, phổ biến và có salt ngẫu nhiên mỗi lần hash)
pwd_context = CryptContext(schemes=["bcrypt"])


# Class để nói đến các behavior liên qua đến người dùng
class UserEntity(User):
    
    MAX_FAILED_ATTEMPTS: ClassVar[int] = 5  # Giới hạn 5 lần nhập mật khẩu
    
   
    def set_password(self, password: str):
        """
        Hash mật khẩu người dùng rồi lluw vào hashed_password
        sau đó cập nhật update_at để biết thời gian thay đổi gần nhất
        """
        self.hashed_password = pwd_context.hash(password)
        self.touch()

        
        
        
    def verify_password(self, password: str) -> bool:
        """
        Kiểm tra mật khẩu. 
            Nếu sai: tăng failed_attempts
            Nếu đúng: reset về 0
            Nếu sai >= 5: khóa tài khoản và raise lỗi       
        """
        
        if not pwd_context.verify(password, self.hashed_password):
            self.failed_attempts += 1
            self.touch()
            
            #kiểm tra nếu sai quá 5 lần thì xóa
            if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                self.is_active = False
                raise ValueError("Bạn đã nhập sai quá 5 lần. Tài khoản tạm khóa, vui lòng liên hệ admin")
            else:
                raise ValueError(f"Mật khẩu sai ({self.failed_attempts}/{self.MAX_FAILED_ATTEMPTS})")
        
        else:
            #Đúng mật khẩu thì reset bộ nhớ
            self.failed_attempts = 0
            self.touch()
            return True
    
    
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
        self.failed_attempts = 0
        self.touch()

        
    def deactivate(self):
        """
        Khóa tài khoản.
        đổi is_active=False
        Cập nhật updated_at

        vd
        Người dùng yêu cầu tạm khóa
        Hệ thống phát hiện vi phạm và admin khóa
        """
        self.is_active = False
        self.touch()
        
    def touch(self):
        """
        ghi ngắn gọn hơn cập nhật thời gian thôi
        """
        self.updated_at = datetime.now(timezone.utc)
        
    def to_safe_dict(self):
        """
        Trả về dict 'an toàn' để gửi ra API/UI, loại bỏ hashed_password

        
        self.model_dump() là phương thức của Pydantic BaseModel giúp chuyển sang dict
        Sau đó ta pop(hashed_password) để giảm rủi ro lộ thông tin
        """
        data = self.model_dump()
        data.pop("hashed_password", None)
        return data    
        
        
    