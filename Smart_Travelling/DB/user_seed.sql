USE travel;

INSERT INTO users (username, email, hashed_password, role)
VALUES
('admin', 'admin@gmail.com', '$2b$12$examplehashadminxxx', 'admin'),
('minh', 'minh@gmail.com', '$2b$12$examplehashminhxxx', 'user');

-- tạo dữ liệu mẫu, nên gán vào workbech

