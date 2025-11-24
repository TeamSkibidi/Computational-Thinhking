document.getElementById("loginBtn").addEventListener("click", () => {
  const user = document.getElementById("username").value.trim();
  const pass = document.getElementById("password").value.trim();

  if (!user || !pass) {
    alert("Vui lòng nhập đầy đủ Username và Password!");
  } else {
    alert(`Xin chào, ${user}!`);
  }
});


 const backBtn = document.getElementById('backBtn');
    
    backBtn.onclick = function() {
        // Chuyển hướng trình duyệt đến file kkk.html
        window.location.href = "../HTML/main.html"; 
    }

       const signinBtn = document.getElementById('signinBtn');
    
    signinBtn.onclick = function() {
        // Chuyển hướng trình duyệt đến file kkk.html
        window.location.href = "../HTML/signin.html"; 
    }





// js 

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Xử lý nút Đăng Nhập (Login)
    const loginBtn = document.getElementById("loginBtn");
    if (loginBtn) {
        loginBtn.addEventListener("click", (event) => {
            // Ngăn form load lại trang nếu nút nằm trong thẻ <form>
            event.preventDefault(); 

            const user = document.getElementById("username").value.trim();
            const pass = document.getElementById("password").value.trim();

            // Kiểm tra rỗng
            if (!user || !pass) {
                alert("Vui lòng nhập đầy đủ Username và Password!");
                return; // Dừng lại, không chạy tiếp
            }

            // --- Kiểm tra tài khoản (Logic giả lập) ---
            // Bạn có thể thay 'admin' và '123456' bằng tài khoản mong muốn
            if (user === 'admin' && pass === '123456') {
                alert(`Xin chào, ${user}! Đăng nhập thành công.`);
                
                // Lưu trạng thái đăng nhập (tùy chọn)
                localStorage.setItem('isLoggedIn', 'true'); 
                
                // Chuyển hướng đến trang chính (Profile hoặc Dashboard)
                // Thay đường dẫn này bằng trang bạn muốn vào sau khi login
                window.location.href = "../profile/profile.html"; 
            } else {
                alert("Sai tên đăng nhập hoặc mật khẩu! (Thử: admin / 123456)");
            }
        });
    }

    // 2. Xử lý nút Quay lại (Back)
    const backBtn = document.getElementById('backBtn');
    if (backBtn) {
        backBtn.onclick = function() {
            window.location.href = "../HTML/main.html"; 
        }
    }

    // 3. Xử lý nút Chuyển sang Đăng ký (Sign In / Sign Up)
    const signinBtn = document.getElementById('signinBtn');
    if (signinBtn) {
        signinBtn.onclick = function() {
            window.location.href = "../HTML/signin.html"; 
        }
    }

});