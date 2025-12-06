from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timezone
import enum

class Role(str, enum.Enum):
    user = "user"
    admin = "admin"

class User(BaseModel):
    # ID duy nhất cho mỗi người dùng (primary key trong database)
    # Optional[int]: có thê là int hoặc None
    # Khi mới tạo user, ID thường chưa có -> database sính sau
    id: Optional[int] = None
    
    # Tên đăng nhập (...) có nghĩa là bắt buộc và có giới hạn độ dài
    # min_lenght=3: ít nhất 3
    # max_length=30: tối đa 30
    username: str = Field(..., min_length=3, max_length=30)
    
    # email người dùng, kiểm tra định dạng email của họ
    email: Optional[EmailStr] = None
    
    # số điện thoại việt nam, có hoặc không cũng được
    # nhưng nếu có thì theo định dạng +84 hoặc 0
    # regex=r"^(?:\+84|0)\d{9,10}$": định dạng +84 và 0 đồng thời là sđt gồm 10 hoặc 11 số
    phone_number: Optional[str] = Field(None, pattern=r"^(?:\+84|0)\d{9,10}$")
    
    # Mật khẩu đã được hash
    hashed_password: str
    
    # Role của người dùng, mặc định là user thường
    role: Role = Role.user
    
    # trạng thái hoạt động - true (vừa tạo tài khoản thì active true cho tài khoản)
    # nếu false thì phải liên lạc bộ phận hỗ trợ
    is_active: bool = True
    
    # Thời điểm tạo tài khoản - tự động lấy tại thời điểm tạo user
    # dùng default_factory đẻ mỗi lần tạo đều sinh thời gian khác nhau
    # datetime.now(timezone.utc) nhằm cho biết đang ở muối giờ nào (vì mình đang ở python hiện đại nên là khuyến khích theo cách này)
    # biến này dùng để admin (sau này mở rông) có quyền coi thử tài khoản được tạo lúc nào
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Thời điểm cập nhật gần nhất — None nếu chưa có thay đổi gì
    # Khi người dùng đổi mật khẩu / thông tin, hệ thống sẽ cập nhật lại
    updated_at: Optional[datetime] = None
    
    #số lần nhập sai
    failed_attempts: int = 0
    
    # tags sở thích người dùng
    Optional[List[str]] = Field(default=None, description="Sở thích: ['Du lịch', 'Ẩm thực', ...]")
    
    
        