from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 1) Import 3 router bạn đã viết
from app.api.v0.routes.auth_router import router as auth_router
from app.api.v0.routes.user_router import router as users_router
from app.api.v0.routes.admin_router import router as admin_router


# 2) Tạo app FastAPI
app = FastAPI(title="Let's Travel API")


# 3) Bật CORS để Frontend gọi được Backend
#    (dev cho phép tất cả origin cho đơn giản)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # FE nào cũng gọi được
    allow_credentials=False,    # để False cho khỏi dính lỗi CORS
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4) Gắn router vào app
#    - router bên trong đã có prefix "/auth", "/users", "/admin"
#    - nên ở đây mình chỉ thêm version "/api/v0"
app.include_router(auth_router, prefix="/api/v0")
app.include_router(users_router, prefix="/api/v0")
app.include_router(admin_router, prefix="/api/v0")


# 5) Serve Frontend (nếu bạn muốn chạy chung BE + FE)
#    Dùng Path để chắc chắn không sai đường dẫn
BASE_DIR = Path(__file__).resolve().parent      # thư mục chứa main.py
FE_DIR = BASE_DIR.parent / "FE"                # ../FE

app.mount(
    "/fe", 
    StaticFiles(directory=str(FE_DIR), html=True),
    name="frontend"
)


# 6) Route test cho biết backend sống
@app.get("/")
def root():
    return {
        "message": "Backend is running!",
        "docs": "/docs",
        "frontend_login": "/fe/html/login.html",
        "frontend_signup": "/fe/html/signin.html"
    }


# 7) Chạy server
#    - bạn có thể chạy bằng: uvicorn app.main:app --reload
#    - hoặc python main.py cũng được
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
