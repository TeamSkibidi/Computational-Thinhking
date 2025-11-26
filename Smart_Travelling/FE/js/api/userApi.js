// usersApi.js
// Chứa các API thuộc router /users

import { request } from "./request.js";

/**
 * LẤY PROFILE
 * GET /users/{user_id}
 */
export async function getProfile(userId) {
  const result = await request(`/users/${userId}`, "GET");
  return result.data; // backend trả data trong result.data
}

/**
 * CẬP NHẬT INFO
 * POST /users/update-info
 */
export function updateInfo(user_id, email, phone_number) {
  const body = { user_id, email, phone_number };
  return request("/users/update-info", "POST", body);
}

/**
 * ĐỔI MẬT KHẨU
 * POST /users/change-password
 */
export function changePassword(user_id, old_password, new_password) {
  const body = { user_id, old_password, new_password };
  return request("/users/change-password", "POST", body);
}
