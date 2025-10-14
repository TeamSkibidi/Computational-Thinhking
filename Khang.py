text = "Hôm nay trời đẹp."

# Mở file ở chế độ ghi nhị phân
with open("output.txt", "wb") as f:
    # Encode chuỗi sang bytes UTF-8 rồi ghi
    f.write(text.encode("utf-8"))

print("✅ Đã ghi xong vào file output.txt theo định dạng UTF-8!")
