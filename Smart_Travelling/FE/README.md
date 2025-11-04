# 🚀 HƯỚNG DẪN CHẠY PROJECT

## 📁 Cấu trúc thư mục
```
d:\FE\
├── index.html          # Giao diện chính
├── style.css           # CSS styling
├── script.js           # JavaScript xử lý (có call API)
├── api_server.py       # FastAPI server
└── requirements.txt    # Dependencies
```

---

## ⚙️ Bước 1: Cài đặt dependencies

Mở PowerShell tại thư mục `d:\FE` và chạy:

```powershell
pip install -r requirements.txt
```

---

## 🖥️ Bước 2: Chạy API Server

### Cách 1: Chạy trực tiếp
```powershell
python api_server.py
```

### Cách 2: Chạy bằng uvicorn (khuyên dùng)
```powershell
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

**Server sẽ chạy tại:** http://localhost:8000

---

## 🌐 Bước 3: Mở Frontend

1. Mở file `index.html` bằng trình duyệt
2. Hoặc dùng Live Server trong VS Code

---

## 🧪 Bước 4: Test thử

### Test API trực tiếp:
- Swagger UI: http://localhost:8000/docs
- API endpoint: http://localhost:8000/api/destinations?city=Hồ Chí Minh&limit=10

### Test Frontend:
1. Click vào nút **"Khám phá điểm đến"**
2. Nhập: **Hồ Chí Minh**
3. Nhấn Search
4. Xem kết quả 10 địa điểm

---

## 📝 Cấu trúc API Response

```json
{
  "status": "success",         // "success" hoặc "error"
  "error_message": null,       // Chỉ có khi status = "error"
  "data": [
    {
      "id": "place_1",
      "name": "Địa điểm 1 tại Hồ Chí Minh",
      "rating": 4.5,
      "reviewCount": 10000,
      "popularity": 90,
      "priceVnd": null,
      "summary": "Mô tả ngắn...",
      "description": null,
      "openTime": "08:00",
      "closeTime": "18:00",
      "phone": "+84 28 38201 001",
      "imageLocalPath": "https://images.unsplash.com/...",
      "address": {
        "houseNumber": "10",
        "street": "Đường số 1",
        "ward": "Phường 1",
        "district": "Quận 1",
        "city": "Hồ Chí Minh",
        "lat": 10.77,
        "lng": 106.69,
        "url": "https://maps.google.com/?q=10.77,106.69"
      }
    }
    // ... 9 địa điểm nữa
  ]
}
```

---

## 🔧 Thay thế hàm ham_1() bằng code thật

Trong file `api_server.py`, tìm hàm `ham_1()` (dòng ~70) và thay thế:

```python
def ham_1(city: str, limit: int) -> List[Dict[str, Any]]:
    """
    THAY THẾ PHẦN NÀY BẰNG CODE THẬT CỦA BẠN
    """
    
    # VD: Gọi database
    return database.get_destinations(city, limit)
    
    # VD: Gọi ML model
    return ml_model.predict(city, limit)
    
    # VD: Web scraping
    return scraper.get_places(city, limit)
```

**Lưu ý:** Hàm phải trả về list gồm 10 dict theo đúng format như trên!

---

## ✅ Kiểm tra lỗi

### Nếu Frontend không gọi được API:
1. **Kiểm tra server có chạy không:**
   ```powershell
   curl http://localhost:8000/health
   ```
   
2. **Kiểm tra CORS:** Mở Console trong trình duyệt (F12), xem có lỗi CORS không

3. **Kiểm tra URL API:** Trong `script.js` dòng 2:
   ```javascript
   const API_URL = 'http://localhost:8000/api/destinations';
   ```

### Nếu API trả về lỗi:
- Xem response trong tab **Network** của DevTools
- Kiểm tra `status` và `error_message` trong JSON response

---

## 🎯 Các tính năng đã hoàn thành

✅ **Frontend:**
- Tìm kiếm địa điểm trên Google Maps (không cần API key)
- Hiển thị địa chỉ tìm được
- Modal gợi ý địa điểm du lịch
- Call API để lấy 10 địa điểm
- Hiển thị kết quả với rating, reviews, giá tiền, giờ mở cửa
- Xử lý lỗi: hiển thị error_message, không có kết quả, không kết nối được server
- Click vào địa điểm để mở Google Maps

✅ **Backend:**
- FastAPI server với CORS đã config
- Endpoint `/api/destinations?city=...&limit=10`
- Validation input tự động (Pydantic)
- Response có `status`, `error_message`, `data`
- Swagger UI để test API
- Hàm `ham_1()` sẵn sàng để thay thế

---

## 🛑 Dừng server

Nhấn `Ctrl+C` trong terminal

---

## 📌 Lưu ý quan trọng

1. **Status trong response:**
   - `"success"`: API thành công, `data` có thể rỗng hoặc có 10 địa điểm
   - `"error"`: API lỗi, `error_message` sẽ mô tả lỗi, `data` = []

2. **Format dữ liệu từ ham_1():**
   - Phải trả về list chứa 10 dict
   - Mỗi dict phải có đầy đủ các field theo Pydantic model
   - Pydantic sẽ tự động validate và báo lỗi nếu thiếu field

3. **Xử lý ảnh:**
   - Hiện tại dùng Unsplash placeholder
   - Nếu muốn dùng ảnh local, đặt trong folder `static/images/`
   - Update `imageLocalPath` thành `"http://localhost:8000/static/images/ten_anh.jpg"`

---

🎉 **Chúc bạn code thành công!**
