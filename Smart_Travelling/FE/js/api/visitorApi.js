// FE/js/api/visitorApi.js
// API gọi tới /api/v0/visitor/recommend

import { request } from "./request.js";

/**
 * Gọi API gợi ý địa điểm theo thành phố.
 *
 * @param {string} city - Tên thành phố (VD: "Hồ Chí Minh")
 * @param {number[]} seenIds - Danh sách id đã gợi ý trước đó
 * @param {number} k - Số lượng địa điểm muốn gợi ý (default 5)
 */
export async function recommendPlaces(city, seenIds = [], k = 5) {
  const body = {
    city,
    seen_ids: seenIds,
    k,
  };

  // request(path, method, body) – giống mấy file api khác
  const res = await request("/visitor/recommend", "POST", body);

  // Backend bạn đang dùng success(...) → { status, message, data }
  // Trả về luôn res.data cho tiện
  return res.data;
}
