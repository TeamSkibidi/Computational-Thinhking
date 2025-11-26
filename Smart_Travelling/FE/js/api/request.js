// request.js - Hàm gọi API chung cho authApi, userApi, adminApi

// Địa chỉ backend FastAPI
export const BASE_URL = "http://localhost:8000/api/v0";

/**
 * Gọi API với fetch
 * @param {string} path - Đường dẫn API, vd: /auth/login
 * @param {string} method - HTTP method: GET, POST, PUT, DELETE
 * @param {object|null} body - Dữ liệu gửi lên (nếu có)
 * @returns {Promise<object>} Response JSON từ backend
 * @throws {Error} Nếu có lỗi từ backend hoặc network
 */


export async function request(path, method = "GET", body = null) {
    // Cấu hình request
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    // Nếu có body thì chuyển sang JSON string
    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    try {
        // Gọi API
        const res = await fetch(BASE_URL + path, options);
        
        //Kiểm tra HTTP status code
        if (!res.ok) {
            // Nếu server trả lỗi HTTP (4xx, 5xx)
            const errorText = await res.text();
            throw new Error(
                `HTTP ${res.status}: ${errorText || res.statusText}`
            );
        }

        // Parse JSON response
        const json = await res.json();

        // Kiểm tra status trong response body
        if (json.status === "error_message") {
            throw new Error(json.error_message || "Unknown error");
        }

        // Trả về data
        return json;

    } catch (error) {
        // Log error để debug ở trang f12
        console.error(`API Error [${method} ${path}]:`, error.message);
        throw error; // Re-throw để caller xử lý
    }
}