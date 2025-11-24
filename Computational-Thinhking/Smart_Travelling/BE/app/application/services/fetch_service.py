import os           #  Để lấy biến mội trường (nới lưu API key)
import time         # Để dùng sleep(): tạm dừng vài giây giữa các lần thử lại (retry)
import requests     # Thư viện gửi request HTTP (GET, POST,...) để gọi API bên ngoài

# retries: số lần thử lại nếu lỗi tạm (mặc định 2)
# timeout: giới hạn thời gian chờ mỗi request (10 giây).
def fetch_from_external_api(url: str, params: dict | None, retries: int = 2, timeout: int = 10 ) -> dict | None:

    for attempt in range (retries + 1):
        try:
            # gửi request
            res =  requests.get(url, params=params, timeout=timeout)

            # Nếu bị giới hạn (rate limit)      quá nhiều request, chờ xí
            if res.status_code == 429:
                print(f"API quá tải (429). Đợi 2s rồi thử lại... ({attempt + 1}/{retries})")
                time.sleep(2)
                continue

            # Kiểm tra các lỗi khác (4xx, 5xx)
            res.raise_for_status()

            # Trả về dữ liệu JSON
            return res.json()
        
        # Bây giờ sẽ đi bắt các ngoại lệ
        except requests.exceptions.Timeout:         #Không nhận đưuọc phản hồi nào
            print(f"Quá thời gian chờ ({attempt+1}/{retries}). Thử lại...")
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"Lỗi gọi API: {e}")
            return None
            
        except Exception as e:
            print(f"Lỗi khác không xác định {e}")
            return None

    print("Gọi API thất bại sau nhiều lần thử")
    return None
        
    


