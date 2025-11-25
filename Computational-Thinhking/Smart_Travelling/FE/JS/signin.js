document.addEventListener("DOMContentLoaded", function () {
    
    // 1. LẤY CÁC THÀNH PHẦN TỪ HTML
    const registerBtn = document.getElementById('registerBtn'); // Nút Đăng ký mới thêm
    const signinBtn = document.getElementById('signinBtn');     // Nút chuyển trang Login
    const backBtn = document.getElementById('backBtn');         // Nút Back

    const emailInput = document.getElementById('email');
    const passInput = document.getElementById('password');
    const repasswordInput = document.getElementById('repassword');

    // --- PHẦN 1: XỬ LÝ ĐĂNG KÝ (Logic sai thì nhập lại) ---
    if (registerBtn) {
        registerBtn.addEventListener('click', function (event) {
            // Ngăn chặn trình duyệt tự tải lại trang
            event.preventDefault();

            // Lấy giá trị người dùng nhập
            const email = emailInput.value.trim();
            const password = passInput.value.trim();
            const repassword = repasswordInput.value.trim();

            // --- BẮT ĐẦU KIỂM TRA (VALIDATION) ---

            // 1. Kiểm tra bỏ trống
            if (email === "" || password === "" || repassword === "") {
                alert("Vui lòng nhập đầy đủ Username và Password!");
                return; // QUAN TRỌNG: Lệnh này dừng chương trình, giữ người dùng ở lại trang để nhập tiếp.
            }

            // 3. Kiểm tra Mật khẩu quá ngắn
            if (password.length < 6) {
                alert("Mật khẩu phải có ít nhất 6 ký tự!");
                passwordInput.value = ""; // Xóa mật khẩu cũ đi
                passwordInput.focus();    // Đưa con trỏ chuột vào ô mật khẩu
                return; // Dừng lại, cho nhập lại
            }
             if (password !== repassword) {
            alert("Mật khẩu nhập lại không khớp!");
            repassInput.value = "";
            repassInput.focus();
            return;
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