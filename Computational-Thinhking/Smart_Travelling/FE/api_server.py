"""
FastAPI Server cho API gợi ý địa điểm du lịch

Cách chạy:
    pip install fastapi uvicorn
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
    
Truy cập:
    http://localhost:8000/api/destinations?city=Hồ Chí Minh&limit=10
    http://localhost:8000/docs (Swagger UI)
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from pathlib import Path
import sys
import os
import httpx  # Để gọi Backend API

# Thêm đường dẫn đến thư mục cha để import BE
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Backend API URL
BACKEND_API_URL = "http://localhost:8000/api/v0/places/search"

# ===== KHỞI TẠO FASTAPI =====
app = FastAPI(
    title="Travel Destination API",
    description="API gợi ý địa điểm du lịch",
    version="1.0.0"
)

# ===== MOUNT STATIC FILES (serve ảnh) =====
images_path = Path(__file__).parent / "images"
images_path.mkdir(exist_ok=True)  # Tạo folder nếu chưa có
app.mount("/images", StaticFiles(directory=str(images_path)), name="images")

# ===== CẤU HÌNH CORS (cho phép frontend gọi API) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== PYDANTIC MODELS =====
class Address(BaseModel):
    """Model cho địa chỉ"""
    street: str
    ward: str
    district: str
    city: str
    lat: float
    lng: float
    url: str

class Destination(BaseModel):
    """Model cho một địa điểm du lịch"""
    id: int
    name: str
    rating: float
    reviewCount: int
    priceVnd: Optional[int] = None
    summary: str
    openTime: str
    closeTime: str
    imageLocalPath: str
    address: Address

class APIResponse(BaseModel):
    """Model cho response API - có thêm status và error_message"""
    status: str  # "success" hoặc "error"
    error_message: Optional[str] = None  # Chỉ có khi status = "error"
    data: List[Destination]  # Danh sách địa điểm (rỗng nếu error)

# ===== HÀM ham_1() CỦA BẠN =====
def ham_1(city: str, limit: int) -> List[Dict[str, Any]]:
    """
    HÀM NÀY BẠN SẼ CODE - Trả về địa điểm theo format chuẩn
    
    Args:
        city: Tên tỉnh/thành phố (VD: "Hồ Chí Minh")
        limit: Số lượng địa điểm muốn lấy
    
    Returns:
        List[Dict]: Danh sách các địa điểm theo format:
        [
            {
                "id": 1,
                "name": "Tên địa điểm",
                "rating": 4.5,
                "reviewCount": 10000,
                "priceVnd": 50000,
                "openTime": "08:00",
                "closeTime": "17:00",
                "summary": "Mô tả ngắn...",
                "imageLocalPath": "http://localhost:8000/images/IMAGE_1.png",
                "address": {
                    "lat": 10.7769,
                    "lng": 106.7009,
                    "street": "Đường ABC",
                    "ward": "Phường XYZ",
                    "district": "Quận 1",
                    "city": "Hồ Chí Minh",
                    "url": "https://www.google.com/maps/search/?api=1&query=10.7769,106.7009"
                }
            }
        ]
    """
    
    # ===== FAKE DATA ĐỂ TEST =====
    fake_data = [
        {
            "id": i,
            "name": f"Địa điểm {i} tại {city}",
            "rating": round(4.5 - (i * 0.05), 1),
            "reviewCount": 10000 - (i * 500),
            "priceVnd": None if i % 2 == 0 else 50000 * i,
            "summary": f"Đây là mô tả ngắn về địa điểm số {i}, một nơi tuyệt vời để khám phá khi đến {city}.",
            "openTime": "08:00",
            "closeTime": "18:00",
            "imageLocalPath": f"http://localhost:8000/images/IMAGE_{i}.png",
            "address": {
                "street": f"Đường số {i}",
                "ward": f"Phường {i}",
                "district": f"Quận {i}",
                "city": city,
                "lat": round(10.77 + (i * 0.01), 6),
                "lng": round(106.69 + (i * 0.01), 6),
                "url": f"https://www.google.com/maps/search/?api=1&query={round(10.77 + (i * 0.01), 6)},{round(106.69 + (i * 0.01), 6)}"
            }
        }
        for i in range(1, limit + 1)
    ]
    
    return fake_data

# ===== ENDPOINT API =====
@app.get("/", tags=["Root"])
async def root():
    """Endpoint gốc - kiểm tra server"""
    return {
        "message": "Travel Destination API đang hoạt động!",
        "docs": "/docs",
        "api_endpoint": "/api/destinations?city=Hồ Chí Minh&limit=10"
    }

@app.get("/api/destinations", response_model=APIResponse, tags=["Destinations"])
async def get_destinations(
    city: str = Query(..., description="Tên tỉnh/thành phố (VD: Hồ Chí Minh)"),
    limit: int = Query(10, ge=1, le=50, description="Số lượng địa điểm (1-50)")
):
    """
    Lấy danh sách địa điểm du lịch theo tỉnh/thành phố
    
    Trả về response với:
    - status: "success" hoặc "error"
    - error_message: Mô tả lỗi (nếu có)
    - data: Danh sách địa điểm (rỗng nếu lỗi)
    """
    
    try:
        # Validate input
        if not city or city.strip() == "":
            return APIResponse(
                status="error",
                error_message="Tham số 'city' không được để trống",
                data=[]
            )
        
        # Gọi Backend API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                BACKEND_API_URL,
                params={"province": city.strip(), "limit": limit},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return APIResponse(
                    status="error",
                    error_message=f"Backend API error: {response.status_code}",
                    data=[]
                )
            
            backend_data = response.json()
            destinations = backend_data.get("data", [])
        
        # Kiểm tra dữ liệu trả về
        if not destinations or len(destinations) == 0:
            return APIResponse(
                status="success",
                error_message=None,
                data=[]
            )
        
        # Sắp xếp theo rating (cao → thấp)
        destinations.sort(key=lambda x: x['rating'], reverse=True)
        
        # Trả về response thành công
        return APIResponse(
            status="success",
            error_message=None,
            data=destinations
        )
        
    except ValueError as val_err:
        # Lỗi validation dữ liệu từ ham_1()
        return APIResponse(
            status="error",
            error_message=f"Dữ liệu không hợp lệ: {str(val_err)}",
            data=[]
        )
        
    except Exception as e:
        # Lỗi không mong muốn
        print(f"❌ ERROR in get_destinations: {e}")
        return APIResponse(
            status="error",
            error_message=f"Lỗi server: {str(e)}",
            data=[]
        )

@app.get("/health", tags=["Health"])
async def health_check():
    """Kiểm tra trạng thái server"""
    return {
        "status": "healthy",
        "service": "Travel Destination API",
        "version": "1.0.0"
    }

# ===== CHẠY SERVER =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
