-- Create places table
-- This table stores information about places (restaurants, attractions, etc.)

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
  category VARCHAR(100) COMMENT 'Category of the place (e.g., restaurant, attraction)',
  dwell INT COMMENT 'Suggested visit duration in minutes',
  image_name VARCHAR(255),
  image_url TEXT COMMENT 'Direct URL to the image',
  tags TEXT COMMENT 'Comma-separated list of tags',
  address_id BIGINT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_place_address FOREIGN KEY (address_id) 
    REFERENCES addresses(id) 
    ON DELETE SET NULL 
    ON UPDATE CASCADE,
  
  -- Indexes for better query performance
  INDEX idx_places_normalized_name (normalized_name),
  INDEX idx_places_rating (rating DESC),
  INDEX idx_places_popularity (popularity DESC),
  INDEX idx_places_price (price_vnd),
  INDEX idx_places_created_at (created_at DESC),
  
  -- Full-text search index
  FULLTEXT INDEX ft_places_name (name, normalized_name),
  FULLTEXT INDEX ft_places_description (summary, description)
  
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add check constraints (MySQL 8.0+)
ALTER TABLE places 
  ADD CONSTRAINT chk_rating CHECK (rating >= 0 AND rating <= 5),
  ADD CONSTRAINT chk_price CHECK (price_vnd >= 0),
  ADD CONSTRAINT chk_review_count CHECK (review_count >= 0),
  ADD CONSTRAINT chk_popularity CHECK (popularity >= 0 AND popularity <= 100),
  ADD CONSTRAINT chk_dwell CHECK (dwell >= 0);