"""
FastAPI Application Entry Point
Travel Place Recommendation API
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Add app directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Setup logging with more detail
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / 'app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Log Python and system info
print("\n" + "="*80)
print("🐍 PYTHON ENVIRONMENT INFO")
print("="*80)
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")
print(f"Working Directory: {os.getcwd()}")
print(f"BASE_DIR: {BASE_DIR}")
print("="*80 + "\n")

# ⭐ IMPORT SAU KHI SETUP LOGGING - QUAN TRỌNG!
from app.infrastructure.database.connection import (
    init_pool,
    close_pool,
    test_connection,
    get_pool_info
)
from app.infrastructure.database.init_db import init_database


# ============================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager - quản lý startup/shutdown events"""
    # ========== STARTUP ==========
    logger.info("=" * 60)
    logger.info("🚀 Starting Travel Place API...")
    logger.info("=" * 60)
    
    try:
        # 1. Kiểm tra environment variables
        logger.info("📋 Checking environment variables...")
        required_vars = ["DB_HOST", "DB_USER", "DB_NAME"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            logger.warning("⚠️  Will use in-memory repository")
        else:
            logger.info(f"✅ Environment: {os.getenv('DB_USER')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
        
        # 2. Khởi tạo database pool (nếu có config)
        if not missing_vars:
            # 2.1 Tạo database và tables nếu chưa tồn tại
            logger.info("🔧 Initializing database schema...")
            await init_database()
            
            logger.info("🔌 Initializing database connection pool...")
            try:
                await init_pool()
                logger.info("✅ Database pool initialized")
                
                # 3. Test connection
                logger.info("🧪 Testing database connection...")
                if await test_connection():
                    logger.info("✅ Database connection verified")
                    pool_info = await get_pool_info()
                    logger.info(f"📊 Pool info: size={pool_info['size']}, free={pool_info['freesize']}")
                else:
                    logger.warning("⚠️  Database connection test failed")
                    
            except Exception as e:
                logger.error(f"❌ Database initialization failed: {e}")
                logger.warning("⚠️  Falling back to in-memory repository")
        
        logger.info("=" * 60)
        logger.info("✅ Application started successfully")
        logger.info(f"📍 Server: http://localhost:8000")
        logger.info(f"📚 API Docs: http://localhost:8000/docs")
        logger.info(f"📖 ReDoc: http://localhost:8000/redoc")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        if os.getenv("ENV", "development") == "production":
            raise
    
    yield
    
    # ========== SHUTDOWN ==========
    logger.info("=" * 60)
    logger.info("🛑 Shutting down application...")
    logger.info("=" * 60)
    
    try:
        await close_pool()
        logger.info("✅ Database pool closed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ Application stopped successfully")
    logger.info("=" * 60)


# ============================================================
# CREATE FASTAPI APP
# ============================================================

app = FastAPI(
    title="Travel Place API",
    version="1.0.0",
    description="""
    ## 🌏 Smart Travel Place Recommendation API
    
    **Features:**
    - 🔍 Smart search with AI + API integration
    - 📍 Place management (CRUD)
    - 🗄️ MySQL database with connection pooling
    - 📊 Statistics and analytics
    
    **Architecture:**
    - Clean Architecture
    - Repository Pattern
    - Dependency Injection
    - Async/Await
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ============================================================
# MIDDLEWARE
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests with error handling"""
    import time
    start_time = time.time()
    
    # Skip favicon requests to avoid errors
    if request.url.path == "/favicon.ico":
        return JSONResponse(status_code=204, content={})
    
    logger.info(f"📥 {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        print(f"\n⚠️ MIDDLEWARE ERROR in {request.method} {request.url.path}")
        print(f"⏱️ Time: {process_time:.3f}s")
        print(f"💥 Error: {type(e).__name__}: {str(e)}\n")
        raise  # Re-raise để exception handler bắt


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors"""
    print("\n" + "="*80)
    print("⚠️ VALIDATION ERROR!")
    print("="*80)
    print(f"Request: {request.method} {request.url}")
    print(f"Validation Errors: {exc.errors()}")
    print("="*80 + "\n")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "errors": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler - Show detailed errors"""
    import traceback
    
    # In đầy đủ traceback ra terminal
    print("\n" + "="*80)
    print("🔥 EXCEPTION CAUGHT!")
    print("="*80)
    print(f"Request: {request.method} {request.url}")
    print(f"Exception Type: {type(exc).__name__}")
    print(f"Exception Message: {str(exc)}")
    print("\n📍 Full Traceback:")
    print("-"*80)
    traceback.print_exc()
    print("="*80 + "\n")
    
    # Log vào file
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    
    # Trả về JSON response
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


# ============================================================
# REGISTER ROUTES
# ============================================================

# ⭐ IMPORT ROUTES SAU KHI TẠO APP - QUAN TRỌNG!
from app.api.v0.routes import places_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.include_router(
    places_router,
    prefix="/api/v0",
    tags=["Places v0"]
)

# Mount static files (images)
static_path = BASE_DIR / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount Frontend files
fe_path = BASE_DIR.parent / "FE"
if fe_path.exists():
    app.mount("/fe", StaticFiles(directory=str(fe_path), html=True), name="frontend")
    logger.info("✅ Frontend mounted at /fe")

logger.info("✅ Routes registered: /api/v0/places")


# ============================================================
# ROOT ENDPOINTS
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """🏠 Root endpoint - API information"""
    return {
        "name": "Travel Place API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "frontend": "/fe/index.html",
        "endpoints": {
            "places": "/api/v0/places",
            "search": "/api/v0/places/search",
            "health": "/health"
        }
    }

@app.get("/index", tags=["Frontend"])
async def frontend():
    """🌐 Serve Frontend HTML"""
    fe_index = BASE_DIR.parent / "FE" / "index.html"
    if fe_index.exists():
        return FileResponse(fe_index)
    return {"error": "Frontend not found"}

@app.get("/health", tags=["Health"])
async def health_check():
    """🏥 Health check endpoint"""
    db_healthy = False
    pool_info = {}
    
    try:
        db_healthy = await test_connection()
        pool_info = await get_pool_info()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": "1.0.0",
        "environment": os.getenv("ENV", "development"),
        "database": {
            "connected": db_healthy,
            "pool": pool_info
        }
    }


@app.get("/info", tags=["Info"])
async def app_info():
    """ℹ️ Application information"""
    return {
        "app": {
            "name": "Travel Place API",
            "version": "1.0.0",
            "description": "Smart travel place recommendation system"
        },
        "environment": {
            "python_version": sys.version,
            "base_dir": str(BASE_DIR),
            "env": os.getenv("ENV", "development")
        },
        "database": {
            "host": os.getenv("DB_HOST", "not configured"),
            "port": os.getenv("DB_PORT", "not configured"),
            "database": os.getenv("DB_NAME", "not configured"),
            "user": os.getenv("DB_USER", "not configured")
        }
    }


# ============================================================
# RUN APPLICATION
# ============================================================
