def read_file(filename):
    try:
        # Mở file ở chế độ đọc
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            print("Nội dung file:")
            print(content)
    except FileNotFoundError:
        print("Lỗi: File không tồn tại.")
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")

# Ví dụ chạy chương trình
file_name = input("Nhập tên file: ")
read_file(file_name)
