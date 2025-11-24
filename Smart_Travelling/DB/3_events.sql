CREATE TABLE IF NOT EXISTS events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    external_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    
    
    lat DECIMAL(10, 7),
    lng DECIMAL(10, 7),

    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    session ENUM('morning', 'afternoon', 'evening', 'full_day') NULL,

    summary TEXT,
    activities JSON NULL,
    image_url VARCHAR(500),
    price_vnd BIGINT,
    popularity INT DEFAULT 0,

    source VARCHAR(100) NOT NULL,              -- tên API / provider

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_events_external (external_id, source),
    INDEX idx_events_city_date (city, start_datetime, end_datetime),
    INDEX idx_events_city_session (city, session)
    );