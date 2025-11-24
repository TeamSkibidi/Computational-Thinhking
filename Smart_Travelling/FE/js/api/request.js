// request.js thì đây là hàm gọi chung của các api khác
// các file authApi/ userApi/ adminApi sẽ dùng lại hàm này

// địa chỉ backend FastAPI
export const BASE_URL = "http://localhost:8000";
// export: là biến này để cho các file khác dùng
// vd: file khác dùng
// import {BASE_URL} from "./request.js"

/**
 *{string} path: đường dẫn api, vd: /auth/login
  {string} method: GET|POST
  {object|null} body: dữ liệu gửi lên nếu có
 */

export async function request(path, method = "GET", body = null){
    // options cấu hình cho fetch sẽ gửi xuống
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };  
    
    
    //nếu có body  thì chuyển sang dạng JSON string
    if(body != null){
        options.body = JSON.stringify(body);        // Chuyển obj Js thành chuỗi JSON
    }

    //gọi fetch
    const res = await fetch(BASE_URL + path, options);  //await laf chowf cho backend trar veef



    // sau khi laays xong bắt đầu lấy các thông tin từ be gửi lên
    const json = await res.json();

    if(json.status == "erroe_message"){
        throw new Error(json.error_message);
    }

    // không lỗi thì trả dữ liệu về
    return json;
}