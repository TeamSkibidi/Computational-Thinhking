USE travel;

CREATE TABLE
    IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(30) NOT NULL UNIQUE,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone_number VARCHAR(15),
        hashed_password VARCHAR(255) NOT NULL,
        role ENUM ('user', 'admin') DEFAULT 'user',
        is_active BOOLEAN DEFAULT TRUE,
        failed_attempts INT DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP
    );

-- dán vào workbench để tạo bảng