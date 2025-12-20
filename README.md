# Smart Travelling - Hệ thống Gợi ý Lịch trình Du lịch Thông minh

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-15+-blue?style=for-the-badge&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/AI-Content--Based%20Filtering-orange?style=for-the-badge" alt="AI">
</p>

---

##  Giới thiệu

**Smart Travelling** là một ứng dụng web giúp người dùng lên kế hoạch du lịch thông minh. Hệ thống sử dụng **AI (Content-Based Filtering)** để gợi ý lịch trình phù hợp với sở thích cá nhân, tối ưu hóa thời gian và khoảng cách di chuyển.

### Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| **Tạo lịch trình tự động** | Gợi ý lịch trình du lịch theo ngày với các địa điểm tham quan, ăn uống |
| **AI Recommendation** | Đề xuất địa điểm dựa trên sở thích (tags) của người dùng |
| **Tùy chỉnh thời gian** | Cho phép bật/tắt và điều chỉnh thời gian từng buổi (sáng, trưa, chiều, tối) |
| **Tối ưu khoảng cách** | Sắp xếp địa điểm gần nhau để tiết kiệm thời gian di chuyển |
| **Ước tính chi phí** | Tính toán tổng chi phí vé tham quan và ăn uống |
| **Lưu lịch sử** | Lưu và xem lại các chuyến đi đã tạo |

---

##  Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (FE)                          │
│              HTML/CSS/JavaScript (Vanilla)                  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST API
┌─────────────────────────▼───────────────────────────────────┐
│                      BACKEND (BE)                           │
│                    FastAPI + Python                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Layer (Routers + Schemas)                      │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Application Layer (Services + AI Engine)           │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Domain Layer (Entities)                            │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Infrastructure Layer (Repositories + Database)     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     DATABASE (DB)                           │
│                      PostgreSQL                             │
│        (Places, Food, Events, Users, Accommodations)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Cài đặt & Chạy

### Yêu cầu
- Python 3.10+
- PostgreSQL 15+
- Node.js (optional, for frontend dev server)

### 1. Clone repository
```bash
git clone <repository-url>
cd Smart_Travelling
```

### 2. Cài đặt Backend
```bash
cd BE

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cấu hình Database
```bash
# Chạy các script SQL theo thứ tự
cd DB
psql -U postgres -d smart_travelling -f 1_addresses.sql
psql -U postgres -d smart_travelling -f 2_places.sql
psql -U postgres -d smart_travelling -f 3_events.sql
psql -U postgres -d smart_travelling -f 4_foodplace.sql
psql -U postgres -d smart_travelling -f 5_accommodation.sql
```

### 4. Chạy Backend
```bash
cd BE
uvicorn main:app --reload --port 8000
```

### 5. Mở Frontend
Mở file `FE/html/main.html` trong trình duyệt hoặc sử dụng Live Server.

---

## Cấu trúc dự án

```
Smart_Travelling/
├── BE/                      # Backend
│   ├── app/
│   │   ├── api/             # REST API endpoints
│   │   ├── application/     # Business logic & AI
│   │   ├── domain/          # Entities
│   │   ├── adapters/        # Repositories
│   │   ├── infrastructure/  # Database
│   │   └── utils/           # Utilities
│   ├── main.py              # Entry point
│   └── requirements.txt
│
├── FE/                      # Frontend
│   ├── html/                # HTML pages
│   ├── css/                 # Stylesheets
│   └── js/                  # JavaScript
│
├── DB/                      # Database scripts
│
└── docs/                    # Documentation
    ├── flowchart_trip_itinerary.md
    └── class_diagram.md
```

---

## API Endpoints

### Trip (Lịch trình)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v0/trip` | Tạo lịch trình du lịch |

### User (Người dùng)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v0/auth/register` | Đăng ký |
| POST | `/api/v0/auth/login` | Đăng nhập |
| GET | `/api/v0/users/{id}` | Lấy thông tin user |
| PUT | `/api/v0/users/{id}/tags` | Cập nhật sở thích |

### Events (Sự kiện)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/v0/events` | Danh sách sự kiện |

### Tags
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/v0/tags` | Danh sách tags |

---

## AI Engine

Hệ thống sử dụng **Content-Based Filtering** để gợi ý địa điểm:

1. **Tag Matching**: So khớp tags của địa điểm với sở thích user
2. **Distance Optimization**: Ưu tiên địa điểm gần vị trí hiện tại
3. **Diversity**: Tránh chọn các địa điểm quá giống nhau
4. **Random Factor**: Thêm yếu tố ngẫu nhiên để tăng đa dạng

---

## Tài liệu

- [Flowchart - Trip Itinerary](docs/flowchart_trip_itinerary.md)
- [Class Diagram](docs/class_diagram.md)

---

## Đội ngũ phát triển

- **Project**: Computational Thinking - Smart Travelling
- **Year**: 2025
- **Members**: - Hcmus
  - Vong Bảo Thắng
  - Nguyễn Hữu Nhật Minh
  - Vũ Huỳnh Đăng Khôi
  - Văn Viết Minh Phú
  - Nguyễn Trong Khang
  - Trương Khánh Duy

---

## License

MIT License - Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

<p align="center">
  Made with for travelers
</p>
