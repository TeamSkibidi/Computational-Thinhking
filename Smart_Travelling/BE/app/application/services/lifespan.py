from app.adapters.repositories.places_repository import fetch_all_places
from app.application.itinerary.itineray_engine import init_ai_recommender
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.domain.entities.place_lite import PlaceLite
from typing import Dict, List, Optional, Tuple

# Load places từ DB để khởi tạo module hybrid recommender
async def load_places_for_ai() -> list[PlaceLite]:
    
    try:
        places = fetch_all_places()
        return places
    except Exception as e:
        print(f" Không load được dữ liệu cho hybrid {e}")
        return []

# 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load places và init AI
    try:
        places = await load_places_for_ai() 
        if places:
            init_ai_recommender(places)
        else:
            print("Không thể load dược địa điểm để khởi tạo AI recommender.")
    except Exception as e:
        print(f"Không thể khởi tạo module recommender: {e}")
    
    yield
    
    # ===== SHUTDOWN =====
    print("Tắt sever")
