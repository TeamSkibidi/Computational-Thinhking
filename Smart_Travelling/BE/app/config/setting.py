import os
from pathlib import Path

DB_DSN = os.getenv("DB_DSN", "postgresql://user:pass@localhost:5432/yourdb")
IMAGE_BASE_URL = "http://localhost:8000/static/place_images/"

MAX_PLACES_PER_BLOCK_DEFAULT = 3
MAX_LEG_DISTANCE_KM_DEFAULT = 5.0

# ✅ THÊM: Định nghĩa BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent.parent

