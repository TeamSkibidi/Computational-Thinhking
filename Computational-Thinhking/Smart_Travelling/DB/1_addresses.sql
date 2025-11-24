-- Create addresses table
-- This table stores address information for places

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
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes for better query performance
CREATE INDEX idx_addresses_city ON addresses(city);
CREATE INDEX idx_addresses_lat_lng ON addresses(lat, lng);
