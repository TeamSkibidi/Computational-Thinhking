-- Create events table
-- Thông tin các sự kiện / lễ hội

CREATE TABLE IF NOT EXISTS events (
<<<<<<< HEAD
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    external_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    
    lat DECIMAL(10, 7),
    lng DECIMAL(10, 7),
=======
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
>>>>>>> origin/main

  external_id VARCHAR(255) NOT NULL,
  name        VARCHAR(255) NOT NULL,

  city   VARCHAR(100) NOT NULL,
  region VARCHAR(100),

<<<<<<< HEAD
    source VARCHAR(100) NOT NULL,    
=======
  -- align với bảng addresses: dùng DOUBLE cho lat/lng
  lat DOUBLE,
  lng DOUBLE,
>>>>>>> origin/main

  start_datetime DATETIME NOT NULL,
  end_datetime   DATETIME NOT NULL,
  session ENUM('morning', 'afternoon', 'evening', 'full_day') NULL,

<<<<<<< HEAD
    UNIQUE KEY uq_events_external (external_id, source),
    INDEX idx_events_city_date (city, start_datetime, end_datetime),
    INDEX idx_events_city_session (city, session)
    );
    
=======
  summary    TEXT,
  activities JSON NULL,
  image_url  VARCHAR(500),

  price_vnd  BIGINT,
  popularity INT DEFAULT 0,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- unique theo external_id + source
  UNIQUE KEY uq_events_external (external_id, source),

  -- index giống addresses (chỉ city)
  INDEX idx_events_city (city),

  -- index phục vụ query theo city + khoảng thời gian
  INDEX idx_events_city_date (city, start_datetime, end_datetime),

  -- index phục vụ query theo city + session
  INDEX idx_events_city_session (city, session)
)
ENGINE=InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
>>>>>>> origin/main
