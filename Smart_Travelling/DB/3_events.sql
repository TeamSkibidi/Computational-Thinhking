-- Create events table
-- Thông tin các sự kiện / lễ hội

CREATE TABLE IF NOT EXISTS events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,

  external_id VARCHAR(255) NOT NULL,
  name        VARCHAR(255) NOT NULL,

  city   VARCHAR(100) NOT NULL,
  region VARCHAR(100),

  -- align với bảng addresses: dùng DOUBLE cho lat/lng
  lat DOUBLE,
  lng DOUBLE,

  start_datetime DATETIME NOT NULL,
  end_datetime   DATETIME NOT NULL,
  session ENUM('morning', 'afternoon', 'evening', 'full_day') NULL,

  summary    TEXT,
  activities JSON NULL,
  image_url  VARCHAR(500),

  price_vnd  BIGINT,
  popularity INT DEFAULT 0,

  -- unique theo external_id 
  UNIQUE KEY uq_events_external (external_id),

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
