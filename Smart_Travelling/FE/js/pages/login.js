// ../js/pages/login.js
// Trang Login - dùng ES module
// Nhiệm vụ:
// 1) Bắt sự kiện submit form login
// 2) Gọi API FastAPI /auth/login bằng hàm login() trong authApi.js
// 3) Lưu user vào localStorage
// 4) Chuyển trang

import { login } from "../api/authApi.js";

// Lấy các element theo id trong HTML
const loginForm = document.getElementById("loginForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

const backBtn = document.getElementById("backBtn");
const signinBtn = document.getElementById("signinBtn");

// ============================
// 1) XỬ LÝ SUBMIT LOGIN FORM
// ============================
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault(); // chặn reload trang khi submit

  // Lấy dữ liệu người dùng nhập
  const username = usernameInput.value.trim();
  const password = passwordInput.value.trim();

  // Kiểm tra rỗng cho chắc
  if (!username || !password) {
    alert("Vui lòng nhập đầy đủ Username và Password!");
    return;
  }

  try {
    // Gọi API login (FastAPI)
    const result = await login(username, password);

    // Nếu login OK
    alert(result.message); // "Đăng nhập thành công!"

    // Backend trả user safe dict ở result.data
    const user = result.data;
    console.log("User login:", user);

    // Lưu user để trang khác xài (tạm thời)
    localStorage.setItem("user", JSON.stringify(user));

    // Chuyển sang trang profile (đổi path nếu bạn đặt khác)
    window.location.href = "../html/main.html";

  } catch (err) {
    // Nếu backend trả lỗi, aut`hApi đã throw Error
    alert("Lỗi đăng nhập: " + err.message);
  }
});

// ============================
// 2) NÚT BACK
// ============================
backBtn.addEventListener("click", () => {
  window.location.href = "../html/main.html";
});

// ============================
// 3) NÚT SIGN UP
// ============================
signinBtn.addEventListener("click", () => {
  window.location.href = "../html/signin.html";
});
