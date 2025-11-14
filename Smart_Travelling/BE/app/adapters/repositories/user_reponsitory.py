from typing import Optional, List, Dict
from app.infrastructure.database.connectdb import get_db



# Tạo tài khoản

def create_user(data: Dict) -> int:
    """

    Tham số:
        data (Dict): chứa các thông tin của user:
            - username (str)
            - email (str)
            - phone_number (str, optional)
            - hashed_password (str)
            - role (str, optional, mặc định = "user")
            - is_active (bool, optional, mặc định = True)
            - failed_attempts (int, optional, mặc định = 0)

    Trả về:
        int: ID của user vừa tạo.
             - Trả về -1 nếu kết nối database thất bại.
    """

    # Lấy connection đến database
    db = get_db()
    if db is None:
        return -1  # Không kết nối được thì trả về -1 mục đích để báo lỗi

    # Tạo cursor để thực thi các câu lệnh SQL
    cursor = db.cursor()

    # Câu lệnh SQL dạng để tránh SQL 
    sql = """
        INSERT INTO users 
        (username, email, phone_number, hashed_password, role, is_active, failed_attempts)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    # Chuẩn bị các giá trị đưa vào SQL
    values = (
        data["username"],
        data["email"],
        data.get("phone_number"),           # .get() để tránh lỗi nếu key không tồn tại
        data["hashed_password"],
        data.get("role", "user"),           # mặc định là user
        data.get("is_active", True),        # mặc định là active
        data.get("failed_attempts", 0)      # mặc định = 0
    )

    # Thực thi câu lệnh 
    cursor.execute(sql, values) # khi thêm vào thì id tự tăng thêm 1 đơn vị

    # Lưu thay đổi vào database
    db.commit()

    # Lấy ID của dòng vừa được thêm
    new_id = cursor.lastrowid 

    # Đóng cursor và connection để tránh rò rỉ tài nguyên
    cursor.close()
    db.close()

    # Trả về ID user mới tạo
    return new_id




# lấy tài khoản user bằng tên

def get_user_by_username(username: str) -> Optional[Dict]:
    # Mỗi lần truy vấn thì mở kết nối DB
    db = get_db()
    if db is None:
        return None

    # cursor(dictionary=True):
    #    Giúp fetchone() trả về dạng dictionary ({"username": "minh"})
    #    Nếu bỏ dictionary=True thì sẽ trả về tuple (("minh",))
    #    Dùng dictionary giúp code rõ ràng hơn và dễ convert sang JSON
    cursor = db.cursor(dictionary=True)

    # Câu SQL lấy user theo username
    sql = "SELECT * FROM users WHERE username = %s"

    # Thực thi câu truy vấn, truyền giá trị vào %s
    cursor.execute(sql, (username,))

    # Lấy đúng 1 dòng kết quả
    result = cursor.fetchone()  # chỗ này đã lấy được thông tin của user

    # Đóng cursor và connection để tránh rò rỉ tài nguyên
    cursor.close()
    db.close()

    # Trả về user hoặc None nếu không có
    return result


# lấy user bằng email mục đíc là lấy ra coi thử email đã bị trùng chưa
# tương tự như username trên nhưng bằng email

def get_user_by_email(email: str) -> Optional[Dict]:
    db = get_db()
    if db is None:
        return None

    cursor = db.cursor(dictionary=True)

    sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(sql, (email,))

    result = cursor.fetchone()# lấy kết quả đó ra

    cursor.close()
    db.close()

    return result


# Lấy tài khoản bằng id của user, tương tự như username
def get_user_by_id(user_id: int) -> Optional[Dict]:
    db = get_db()
    if db is None:
        return None

    cursor = db.cursor(dictionary=True)

    sql = "SELECT * FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))

    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result


# Update các trường hợp

# update email (đổi email)
def update_user_email(user_id: int, new_email: str) -> bool:
    db = get_db()
    if db is None:
        return False

    cursor = db.cursor()
    
    sql = "UPDATE users SET email = %s WHERE id = %s"
    cursor.execute(sql, (new_email, user_id))
    
    db.commit()

    updated = cursor.rowcount > 0       # phần này để kiểm tra số dòng thay đổi

    cursor.close()
    db.close()

    return updated

# update số điện thoại
def update_user_phone(user_id: int, phone: str) -> bool:
    db = get_db()
    if db is None:
        return False

    cursor = db.cursor()
    sql = "UPDATE users SET phone_number = %s WHERE id = %s"
    cursor.execute(sql, (phone, user_id))
    db.commit()

    updated = cursor.rowcount > 0

    cursor.close()
    db.close()

    return updated


# update mật khẩu
def update_user_password(user_id: int, hashed_password: str) -> bool:
    db = get_db()
    if db is None:
        return False

    cursor = db.cursor()
    sql = "UPDATE users SET hashed_password = %s WHERE id = %s"
    cursor.execute(sql, (hashed_password, user_id))
    db.commit()

    updated = cursor.rowcount > 0

    cursor.close()
    db.close()

    return updated


# reset lại số lần nhập sai về 0 nếu đăng nhập thành công
def reset_failed_attempts(user_id: int) -> bool:
    db = get_db()
    if db is None:
        return False

    cursor = db.cursor()
    sql = "UPDATE users SET failed_attempts = 0 WHERE id = %s"
    cursor.execute(sql, (user_id,))
    db.commit()

    updated = cursor.rowcount > 0

    cursor.close()
    db.close()

    return updated

