USE travel;

CREATE TABLE IF NOT EXISTS food (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  summary VARCHAR(160),
  description TEXT,
  rating DECIMAL(3,2),
  reviewCount INT DEFAULT 0,
  popularity INT DEFAULT 0,
  image_url VARCHAR(500),
  tags JSON,
  openTime CHAR(5),
  closeTime CHAR(5),
  priceVND BIGINT,
  image_name VARCHAR(255),

  address_id BIGINT,
  category ENUM('visit','eat','hotel') NOT NULL DEFAULT 'visit',

  cuisine_type VARCHAR(100),
  phone VARCHAR(50),
  menu_url VARCHAR(500),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_food_address FOREIGN KEY (address_id)
    REFERENCES addresses(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

  INDEX idx_food_name (name),
  INDEX idx_food_category (category),
  INDEX idx_food_rating (rating),
  INDEX idx_food_popularity (popularity),

  CONSTRAINT chk_food_rating CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5)),
  CONSTRAINT chk_food_review CHECK (reviewCount >= 0),
  CONSTRAINT chk_food_popularity CHECK (popularity IS NULL OR (popularity >= 0 AND popularity <= 100)),
  CONSTRAINT chk_food_price CHECK (priceVND IS NULL OR priceVND >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;