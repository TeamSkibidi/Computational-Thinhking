USE travel;

CREATE TABLE IF NOT EXISTS accommodation (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  priceVND BIGINT,
  summary VARCHAR(160),
  description TEXT,
  rating DECIMAL(3,2),
  reviewCount INT DEFAULT 0,
  popularity INT DEFAULT 0,
  image_url VARCHAR(500),
  phone VARCHAR(50),
  tags JSON,
  category ENUM('visit','eat','hotel') NOT NULL DEFAULT 'hotel',
  capacity INT,                 
  num_guest INT,

  address_id BIGINT,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- FK
  CONSTRAINT fk_accommodation_address FOREIGN KEY (address_id)
    REFERENCES addresses(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,

  -- Indexes
  INDEX idx_accommodation_name (name),
  INDEX idx_accommodation_category (category),
  INDEX idx_accommodation_rating (rating),
  INDEX idx_accommodation_popularity (popularity),
  -- Checks
  CONSTRAINT chk_accommodation_rating CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5)),
  CONSTRAINT chk_accommodation_review CHECK (reviewCount >= 0),
  CONSTRAINT chk_accommodation_popularity CHECK (popularity IS NULL OR (popularity >= 0 AND popularity <= 100)),
  CONSTRAINT chk_accommodation_price CHECK (priceVND IS NULL OR priceVND >= 0),
  CONSTRAINT chk_accommodation_capacity CHECK (capacity IS NULL OR capacity >= 1),
  CONSTRAINT chk_accommodation_nightly CHECK (priceVND IS NULL OR priceVND >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;