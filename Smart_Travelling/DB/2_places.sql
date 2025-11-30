CREATE TABLE IF NOT EXISTS places (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  priceVND BIGINT,
  summary VARCHAR(160),
  description TEXT,
  openTime CHAR(5),
  closeTime CHAR(5),
  phone VARCHAR(50),
  rating DECIMAL(3,2),
  reviewCount INT DEFAULT 0,
  popularity INT DEFAULT 0,
  image_url VARCHAR(500),
  tags JSON,

  category ENUM('visit','eat','hotel') NOT NULL DEFAULT 'visit',
  dwell INT,

  address_id BIGINT,

>>>>>>> main
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_place_address FOREIGN KEY (address_id)
    REFERENCES addresses(id)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  INDEX idx_places_name (name),
  INDEX idx_places_rating (rating DESC),
  INDEX idx_places_popularity (popularity DESC),
  INDEX idx_places_category (category),
  INDEX idx_places_created_at (created_at DESC),
  FULLTEXT INDEX ft_places_text (name, summary, description),
  CONSTRAINT chk_rating CHECK (rating IS NULL OR rating BETWEEN 0 AND 5),
  CONSTRAINT chk_reviewCount CHECK (reviewCount >= 0),
  CONSTRAINT chk_popularity CHECK (popularity BETWEEN 0 AND 100),
  CONSTRAINT chk_priceVND CHECK (priceVND IS NULL OR priceVND >= 0),
  CONSTRAINT chk_dwell CHECK (dwell IS NULL OR dwell >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;