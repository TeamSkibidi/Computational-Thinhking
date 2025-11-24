import os           #Thư viện dùng để làm việc với file, thư mục và đường dẫn trong máy tính
import requests     #Thư viện gửi request HTTP (nói chuyện với internet)

DEFAULT_IMAGE_PATH = "static/images/default.jpg"


def download_image(image_url: str | None, save_path: str) -> str:

    #B1: kiểm tra xem url ảnh có tồn tại hay không
    if not image_url:
        print("Không có URL ảnh, sẽ dùng ảnh mặc định")
        return DEFAULT_IMAGE_PATH
    
    #B2: Nếu có URL ảnh thì
    try:
        print(f"Đang tải ảnh từ url: {image_url}")

        # Gửi request HTTP get đến server để lấy ảnh xuống
        # timeout=10 là sau 10 giây không phản hồi sẽ ngắt
        reponse = requests.get(image_url, timeout=10)

        # Kiểm tra mã trạng thái của phản hồi, nếu có lỗi thì ném 1 EXEPTION
        # 200 -> Thành công
        # 404 -> Không tìm thấy (Not found)
        # 500 -> Lỗi máy chủ (Internal Server Eror)
        # 403 -> Bị từ chối truy cập (Forbidden)
        reponse.raise_for_status()


        #B3: Nếu tải thành công thì ta tiến hành lưu ảnh ra file

        # Đảm bảo thư mục tồn tại, nhằm tránh lỗi nếu không có thư mục, nếu chwua có thì mình sẽ tạo
        # os.path.dirname(save_path): lấy đường dẫn thư mục cha của file đó (vd static/images/avatar.jpg là lấy static/images)
        # os.makedirs(...)          : tạo thư mục và các thư mục con nếu có
        # exit_ok=True              : Nếu thư mục tồn tại rồi thì không báo lỗi
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Mở file theo chế độ ghi nhị phân ("wb" = write binary)
        # with ... as               : tự đóng file sau khi khối with kết thúc kể cả khi có lỗi xảy ra
        # reponse.content           : nội dung ảnh nhận từu server (dạng bytes)
        # file.write(...)           : ghi nội dung vào file
        with open(save_path, "wb") as file:
            file.write(reponse.content)

        print(f"Ảnh đã được tải và lưu tại {save_path}")
        return save_path
    

    #B4: tại đây sẽ bắt tất cả lỗi có thể xảy ra trong quá trình tải ảnh
    except requests.exceptions.Timeout:
        print("ERROR: Quá thời gian chờ khi tải ảnh (timeout). Dùng ảnh mặt định")
    except requests.exceptions.HTTPError as e:
        print(f"Lỗi HTTP: {e}. Dùng ảnh mặc định")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khác trong quá trình tải ảnh: {e}. Dùng ảnh mặc định")
    except Exception as e:
        print(f"Lỗi không xác định: {e}. Dùng ảnh mặc định")
    

    return DEFAULT_IMAGE_PATH



        



    




    