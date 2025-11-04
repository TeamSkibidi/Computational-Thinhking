"""
Database initialization module
Tự động tạo database và tables nếu chưa tồn tại
"""
import aiomysql
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# SQL để tạo bảng addresses
CREATE_ADDRESSES_TABLE = """
CREATE TABLE IF NOT EXISTS addresses (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  house_number VARCHAR(50),
  street VARCHAR(255),
  ward VARCHAR(100),
  district VARCHAR(100),
  city VARCHAR(100),
  lat DOUBLE,
  lng DOUBLE,
  url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX idx_addresses_city (city),
  INDEX idx_addresses_lat_lng (lat, lng)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# SQL để tạo bảng places
CREATE_PLACES_TABLE = """
CREATE TABLE IF NOT EXISTS places (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  normalized_name VARCHAR(255) NOT NULL,
  price_vnd BIGINT,
  summary TEXT,
  description TEXT,
  open_time CHAR(5) COMMENT 'Format: HH:MM',
  close_time CHAR(5) COMMENT 'Format: HH:MM',
  phone VARCHAR(50),
  rating DECIMAL(3,2) COMMENT 'Rating from 0.00 to 5.00',
  review_count INT DEFAULT 0,
  popularity INT DEFAULT 0,
  image_name VARCHAR(255),
  address_id BIGINT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_place_address FOREIGN KEY (address_id) 
    REFERENCES addresses(id) 
    ON DELETE SET NULL 
    ON UPDATE CASCADE,
  
  INDEX idx_places_normalized_name (normalized_name),
  INDEX idx_places_rating (rating DESC),
  INDEX idx_places_popularity (popularity DESC),
  INDEX idx_places_price (price_vnd),
  INDEX idx_places_created_at (created_at DESC),
  
  FULLTEXT INDEX ft_places_name (name, normalized_name),
  FULLTEXT INDEX ft_places_description (summary, description)
  
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# SQL để thêm constraints
ADD_CONSTRAINTS = """
ALTER TABLE places 
  ADD CONSTRAINT IF NOT EXISTS chk_rating CHECK (rating >= 0 AND rating <= 5),
  ADD CONSTRAINT IF NOT EXISTS chk_price CHECK (price_vnd >= 0),
  ADD CONSTRAINT IF NOT EXISTS chk_review_count CHECK (review_count >= 0),
  ADD CONSTRAINT IF NOT EXISTS chk_popularity CHECK (popularity >= 0);
"""


async def init_database():
    """
    Khởi tạo database và tables
    Tự động tạo nếu chưa tồn tại
    """
    try:
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = int(os.getenv("DB_PORT", 3306))
        db_user = os.getenv("DB_USER", "root")
        db_pass = os.getenv("DB_PASS", "")
        db_name = os.getenv("DB_NAME", "travel")
        
        logger.info(f"🔧 Checking database '{db_name}'...")
        
        # 1. Kết nối đến MySQL server (không chọn database cụ thể)
        conn = await aiomysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            autocommit=True
        )
        
        async with conn.cursor() as cursor:
            # 2. Tạo database nếu chưa tồn tại
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {db_name} "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            logger.info(f"✅ Database '{db_name}' ready")
            
            # 3. Chọn database
            await cursor.execute(f"USE {db_name}")
            
            # 4. Tạo bảng addresses
            logger.info("🔧 Creating table 'addresses'...")
            await cursor.execute(CREATE_ADDRESSES_TABLE)
            logger.info("✅ Table 'addresses' ready")
            
            # 5. Tạo bảng places
            logger.info("🔧 Creating table 'places'...")
            await cursor.execute(CREATE_PLACES_TABLE)
            logger.info("✅ Table 'places' ready")
            
            # 6. Thêm constraints (bỏ qua lỗi nếu đã tồn tại)
            try:
                # Kiểm tra xem constraint đã tồn tại chưa
                await cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'places' 
                    AND CONSTRAINT_NAME = 'chk_rating'
                """, (db_name,))
                result = await cursor.fetchone()
                
                if result[0] == 0:
                    # Chưa có constraint, thêm vào
                    await cursor.execute("""
                        ALTER TABLE places 
                          ADD CONSTRAINT chk_rating CHECK (rating >= 0 AND rating <= 5),
                          ADD CONSTRAINT chk_price CHECK (price_vnd >= 0),
                          ADD CONSTRAINT chk_review_count CHECK (review_count >= 0),
                          ADD CONSTRAINT chk_popularity CHECK (popularity >= 0)
                    """)
                    logger.info("✅ Constraints added")
                else:
                    logger.debug("✅ Constraints already exist")
            except Exception as e:
                logger.debug(f"Constraints setup: {e}")
        
        conn.close()
        logger.info("✅ Database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
