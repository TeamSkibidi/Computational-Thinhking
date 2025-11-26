// ../js/pages/signin.js (ES module)

import { register } from "../api/authApi.js";

document.addEventListener("DOMContentLoaded", function () {

  // 1) Lấy form và input
  const signupForm = document.getElementById("signupForm");
  const backBtn = document.getElementById("backBtn");

  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const rePasswordInput = document.getElementById("repassword")

  // 2) Bắt submit của form (chuẩn hơn bắt click)
  signupForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    const rePassword = rePasswordInput.value.trim();


    // ===== VALIDATION như bạn làm =====
    if (username === "" || password === "" || rePassword === "") {
      alert("Vui lòng nhập đầy đủ Username, Password và Prepassword!");
      return;
    }

   
    if (password.length < 6 || rePassword.length < 6) {
      alert("Mật khẩu phải có ít nhất 6 ký tự!");
      passwordInput.value = "";
      rePasswordInput.value = "";
      passwordInput.focus();
      return;
    }

    if (password != rePassword){
        alert("Mật khẩu nhập lại không đúng, nhập lại")
        rePasswordInput.value = "";
        rePasswordInput.focus();
        return;
    }


    // ===== hết validation =====

    try {
      // 3) Gọi backend để đăng ký thật
      // Backend bạn chỉ cần username + password
      const result = await register(username, password);

      alert(result.message); 
      // ví dụ: "Đăng ký thành công. Vui lòng đăng nhập!"

      // 4) Chuyển trang
      window.location.href = "../html/login.html";

    } catch (err) {
      alert("Đăng ký thất bại: " + err.message);
    }
  });

  // 3) Nút back
  backBtn.addEventListener("click", function () {
    window.location.href = "../html/login.html";
  });
});
