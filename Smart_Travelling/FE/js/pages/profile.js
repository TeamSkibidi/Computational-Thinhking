// ../js/profile.js
// Trang Profile - ES Module
// Mục tiêu:
// 1) Lấy thông tin user đã login (lưu trong localStorage).
// 2) Gọi backend lấy profile thật.
// 3) Hiển thị dữ liệu ra UI.
// 4) Cho sửa email, phone, đổi password.
// 5) Có hàm switchTab và logout vì HTML gọi inline.

import { getProfile, updateInfo, changePassword } from "../api/userApi.js";

// ============================
// 0) LẤY USER ĐÃ LOGIN TỪ LOCALSTORAGE
// ============================
const savedUser = localStorage.getItem("user");
// localStorage là nơi mình lưu user sau khi login thành công.
// getItem("user") sẽ lấy chuỗi JSON user ra (nếu có).

if (!savedUser) {
  alert("Bạn chưa đăng nhập!");
  window.location.href = "../html/login.html";
}

const user = JSON.parse(savedUser);
// chuyển thành dạng JSON
const userId = user.id;

// ============================
// 1) LẤY PROFILE TỪ BACKEND + HIỂN THỊ
// ============================
let currentProfile = null; // lưu profile hiện tại để dùng khi edit

async function loadProfile() {
  try {
    const profile = await getProfile(userId);
    currentProfile = profile;

    // Username + role
    document.getElementById("profileUsername").innerText = profile.username;
    document.getElementById("profileRole").innerText = profile.role;

    // Email
    document.getElementById("emailText").innerText =
      profile.email ? profile.email : "Chưa có email";

    // Phone
    document.getElementById("phoneText").innerText =
      profile.phone_number ? profile.phone_number : "Chưa có số điện thoại";

    

  } catch (err) {
    alert("Lỗi load profile: " + err.message);
  }
}

loadProfile();

// ============================
// 2) EDIT EMAIL (UI + CALL API)
// ============================
const editEmailBtn = document.getElementById("editEmailBtn");
const emailEditBox = document.getElementById("emailEditBox");
const oldEmailBox = document.getElementById("oldEmailBox");
const oldEmailInput = document.getElementById("oldEmailInput");
const newEmailInput = document.getElementById("newEmailInput");
const saveEmailBtn = document.getElementById("saveEmailBtn");
const cancelEmailBtn = document.getElementById("cancelEmailBtn");

editEmailBtn.addEventListener("click", () => {
  // hiện box edit
  emailEditBox.classList.remove("hidden");

  // nếu đã có email cũ thì show
  if (currentProfile?.email) {
    oldEmailBox.classList.remove("hidden");
    oldEmailInput.value = currentProfile.email;
  } else {
    oldEmailBox.classList.add("hidden");
    oldEmailInput.value = "";
  }

  newEmailInput.value = "";
});

cancelEmailBtn.addEventListener("click", () => {
  // ẩn box edit
  emailEditBox.classList.add("hidden");
  newEmailInput.value = "";
});

saveEmailBtn.addEventListener("click", async () => {
  const newEmail = newEmailInput.value.trim();

  // cho phép xóa email (nhập rỗng) hoặc nhập email mới
  try {
    const result = await updateInfo(userId, newEmail, currentProfile?.phone_number);
    alert(result.message);

    emailEditBox.classList.add("hidden");
    await loadProfile(); // load lại UI

  } catch (err) {
    alert("Lỗi cập nhật email: " + err.message);
  }
});

// ============================
// 3) EDIT PHONE (UI + CALL API)
// ============================
const editPhoneBtn = document.getElementById("editPhoneBtn");
const phoneEditBox = document.getElementById("phoneEditBox");
const oldPhoneBox = document.getElementById("oldPhoneBox");
const oldPhoneInput = document.getElementById("oldPhoneInput");
const newPhoneInput = document.getElementById("newPhoneInput");
const savePhoneBtn = document.getElementById("savePhoneBtn");
const cancelPhoneBtn = document.getElementById("cancelPhoneBtn");

editPhoneBtn.addEventListener("click", () => {
  phoneEditBox.classList.remove("hidden");

  if (currentProfile?.phone_number) {
    oldPhoneBox.classList.remove("hidden");
    oldPhoneInput.value = currentProfile.phone_number;
  } else {
    oldPhoneBox.classList.add("hidden");
    oldPhoneInput.value = "";
  }

  newPhoneInput.value = "";
});

cancelPhoneBtn.addEventListener("click", () => {
  phoneEditBox.classList.add("hidden");
  newPhoneInput.value = "";
});

savePhoneBtn.addEventListener("click", async () => {
  const newPhone = newPhoneInput.value.trim();

  try {
    const result = await updateInfo(userId, currentProfile?.email, newPhone);
    alert(result.message);

    phoneEditBox.classList.add("hidden");
    await loadProfile();

  } catch (err) {
    alert("Lỗi cập nhật số điện thoại: " + err.message);
  }
});

// ============================
// 4) CHANGE PASSWORD (CALL API)
// ============================
const oldPasswordInput = document.getElementById("oldPasswordInput");
const newPasswordInput = document.getElementById("newPasswordInput");
const reNewPasswordInput = document.getElementById("reNewPasswordInput");
const changePasswordBtn = document.getElementById("changePasswordBtn");

changePasswordBtn.addEventListener("click", async () => {
  const oldPass = oldPasswordInput.value.trim();
  const newPass = newPasswordInput.value.trim();
  const reNewPass = reNewPasswordInput.value.trim();

  // validation đơn giản
  if (!oldPass || !newPass || !reNewPass) {
    alert("Vui lòng nhập đủ 3 ô mật khẩu!");
    return;
  }

  if (newPass.length < 6) {
    alert("Mật khẩu mới phải >= 6 ký tự!");
    return;
  }

  if (newPass !== reNewPass) {
    alert("Xác nhận mật khẩu mới không khớp!");
    reNewPasswordInput.value = "";
    reNewPasswordInput.focus();
    return;
  }

  if (newPass === oldPass){
    alert("Mật khẩu mới không được giống mật khẩu cũ!")
    newPasswordInput.value = "";
    reNewPasswordInput.value = "";
    newPasswordInput.focus();
    return;
  }

  try {
    const result = await changePassword(userId, oldPass, newPass);
    alert(result.message);

    // clear input sau khi đổi xong
    oldPasswordInput.value = "";
    newPasswordInput.value = "";
    reNewPasswordInput.value = "";

  } catch (err) {
    alert("Lỗi đổi mật khẩu: " + err.message);
  }
});


// ============================
// 5) SWITCH TAB (HTML đang gọi inline)
// ============================
// HTML có onclick="switchTab('tab-general', this)"
window.switchTab = function(tabId, element) {
  // Ẩn tất cả content-section
  document.querySelectorAll(".content-section").forEach(sec => {
    sec.classList.remove("active");
  });

  // Bỏ active của tất cả nav-link
  document.querySelectorAll(".nav-link").forEach(link => {
    link.classList.remove("active");
  });

  // Hiện tab được chọn
  document.getElementById(tabId).classList.add("active");

  // Thêm active cho link được click
  element.classList.add("active");
};

// ============================
// 6) LOGOUT (HTML đang gọi inline)
// ============================
window.logout = function() {
  localStorage.removeItem("user");
  alert("Đã đăng xuất!");
  window.location.href = "../html/login.html";
};
