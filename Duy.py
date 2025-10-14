with open("output.txt", "w", encoding="utf-8") as f:
    # Bài 1: Xuất dòng chữ "I'm a student"
    f.write("I'm a student\n")

    # Bài 2: Xuất giá trị 1/7 với 5 chữ số thập phân
    f.write("%.5f\n\n" % (1/7))

    # Bài 3: Nhập 2 số nguyên, ghi tổng ra file
    a = int(input("Nhập số thứ nhất: "))
    b = int(input("Nhập số thứ hai: "))
    tong = a + b
    f.write("Tổng hai số là: %d\n\n" % tong)

    # Bài 4: Nhập tên file, đọc nội dung nếu có
    filename = input("Nhập tên file cần đọc: ")
    try:
        with open(filename, "r", encoding="utf-8") as fin:
            data = fin.read()
            f.write("Nội dung file:\n" + data + "\n")
    except:
        f.write("File không tồn tại.\n")
