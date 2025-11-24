"""Database connection pool management using aiomysql"""
import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import aiomysql

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[aiomysql.Pool] = None


async def init_pool():
    """
    Khởi tạo connection pool khi start app
    
    Gọi trong lifespan event của FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await init_pool()
            yield
            await close_pool()
    """
    global _pool
    
    if _pool is not None:
        logger.warning("Database pool already initialized")
        return
    
    try:
        _pool = await aiomysql.create_pool(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            db=os.getenv("DB_NAME", "travel"),
            charset='utf8mb4',
            autocommit=False,
            minsize=int(os.getenv("DB_POOL_MIN_SIZE", "5")),
            maxsize=int(os.getenv("DB_POOL_MAX_SIZE", "20")),
            connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
        )
        logger.info(
            f"✅ Database pool initialized: "
            f"{os.getenv('DB_USER', 'root')}@{os.getenv('DB_HOST', '127.0.0.1')}/"
            f"{os.getenv('DB_NAME', 'travel')}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize database pool: {e}")
        raise


async def close_pool():
    """
    Đóng connection pool khi shutdown app
    
    Gọi trong lifespan event của FastAPI
    """
    global _pool
    
    if _pool is None:
        logger.warning("Database pool not initialized")
        return
    
    _pool.close()
    await _pool.wait_closed()
    _pool = None
    logger.info("✅ Database pool closed")


@asynccontextmanager
async def get_connection() -> AsyncGenerator[aiomysql.Connection, None]:
    """
    Context manager để lấy database connection từ pool
    
    Auto-commit khi không có exception, auto-rollback khi có lỗi
    
    Usage:
        async with get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM places")
                results = await cur.fetchall()
    
    Raises:
        RuntimeError: Nếu pool chưa được khởi tạo
        Exception: Database errors
    """
    global _pool
    
    # Kiểm tra pool đã khởi tạo chưa
    if _pool is None:
        logger.warning("Database pool not initialized, initializing now...")
        await init_pool()
    
    # Lấy connection từ pool
    async with _pool.acquire() as conn:
        try:
            # Yield connection cho caller sử dụng
            yield conn
            
            # Auto-commit nếu không có exception
            await conn.commit()
            logger.debug("Transaction committed")
            
        except Exception as e:
            # Auto-rollback nếu có lỗi
            await conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise


async def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        bool: True nếu kết nối thành công
    """
    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                logger.info(f"✅ Database connection test successful: {result}")
                return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False


async def get_pool_info() -> dict:
    """
    Lấy thông tin về connection pool
    
    Returns:
        dict: Thông tin pool (size, freesize, maxsize)
    """
    global _pool
    
    if _pool is None:
        return {
            "initialized": False,
            "size": 0,
            "freesize": 0,
            "maxsize": 0,
            "minsize": 0
        }
    
    return {
        "initialized": True,
        "size": _pool.size,
        "freesize": _pool.freesize,
        "maxsize": _pool.maxsize,
        "minsize": _pool.minsize
    }
