document.addEventListener("DOMContentLoaded", function () {
    
    // 1. LẤY CÁC THÀNH PHẦN TỪ HTML
    const registerBtn = document.getElementById('registerBtn'); // Nút Đăng ký mới thêm
    const signinBtn = document.getElementById('signinBtn');     // Nút chuyển trang Login
    const backBtn = document.getElementById('backBtn');         // Nút Back

    const emailInput = document.getElementById('email');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    // --- PHẦN 1: XỬ LÝ ĐĂNG KÝ (Logic sai thì nhập lại) ---
    if (registerBtn) {
        registerBtn.addEventListener('click', function (event) {
            // Ngăn chặn trình duyệt tự tải lại trang
            event.preventDefault();

            // Lấy giá trị người dùng nhập
            const email = emailInput.value.trim();
            const username = usernameInput.value.trim();
            const password = passwordInput.value.trim();

            // --- BẮT ĐẦU KIỂM TRA (VALIDATION) ---

            // 1. Kiểm tra bỏ trống
            if (email === "" || username === "" || password === "") {
                alert("Vui lòng nhập đầy đủ Email, Username và Password!");
                return; // QUAN TRỌNG: Lệnh này dừng chương trình, giữ người dùng ở lại trang để nhập tiếp.
            }

            // 2. Kiểm tra Email có hợp lệ không (phải có @)
            if (!email.includes("@")) {
                alert("Email không hợp lệ (thiếu @)!");
                return; // Dừng lại, cho nhập lại
            }

            // 3. Kiểm tra Mật khẩu quá ngắn
            if (password.length < 6) {
                alert("Mật khẩu phải có ít nhất 6 ký tự!");
                passwordInput.value = ""; // Xóa mật khẩu cũ đi
                passwordInput.focus();    // Đưa con trỏ chuột vào ô mật khẩu
                return; // Dừng lại, cho nhập lại
            }

            // --- NẾU ĐÚNG HẾT MỌI THỨ ---
            alert("Đăng ký thành công! Đang chuyển hướng...");
            // Lúc này mới cho phép chuyển trang
            window.location.href = "../HTML/login.html"; // Sửa đường dẫn này đúng với thư mục của bạn
        });
    }

    

    // --- PHẦN 2: XỬ LÝ NÚT BACK ---
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            window.location.href = "../HTML/login.html"; 
        });
    }
});