// adminApi.js
// Chứa các API thuộc router /admin

import { request } from "./request.js";

/**
 * ADMIN XEM DANH SÁCH USER
 * GET /admin/users
 */
export async function adminListUsers() {
  const result = await request("/admin/users", "GET");
  return result.data;
}

/**
 * ADMIN KHÓA USER
 * POST /admin/users/deactivate/{user_id}
 */
export function adminDeactivateUser(userId) {
  return request(`/admin/users/deactivate/${userId}`, "POST");
}

/**
 * ADMIN MỞ KHÓA USER
 * POST /admin/users/activate/{user_id}
 */
export function adminActivateUser(userId) {
  return request(`/admin/users/activate/${userId}`, "POST");
}

/**
 * ADMIN XÓA USER
 * POST /admin/users/delete/{user_id}
 */
export function adminDeleteUser(userId) {
  return request(`/admin/users/delete/${userId}`, "POST");
}
