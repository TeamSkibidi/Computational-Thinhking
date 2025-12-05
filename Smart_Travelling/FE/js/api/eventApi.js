// eventApi.js
// Chứa các API thuộc router /events

import { request } from "./request.js";

/**
 * TÌM KIẾM LỄ HỘI THEO TÊN
 * GET /events/search-by-name?keyword=...&limit=...
 */
export async function searchEventByName(keyword, limit = 5) {
  if (!keyword) {
    return [];
  }

  const query = new URLSearchParams({
    keyword,
    limit: String(limit),
  }).toString();

  const result = await request(`/events/search-by-name?${query}`, "GET");
  return result.data;
}

/**
 * LẤY DANH SÁCH SỰ KIỆN
 * GET /events?city=...&target_date=...&session=...&sort=...
 **/
export async function listEvents(params = {}) {
  const { city, target_date, session, sort } = params;

  if (!city || !target_date) {
    throw new Error("city và target_date là bắt buộc khi gọi listEvents()");
  }

  const queryObj = {
    city,
    target_date,
  };

  if (session) queryObj.session = session;
  if (sort) queryObj.sort = sort;

  const query = new URLSearchParams(queryObj).toString();
  const path = `/events/list_event?${query}`;

  const result = await request(path, "GET");
  return result.data; 
}

/**
 * GỢI Ý SỰ KIỆN THEO KHOẢNG CÁCH / ĐỘ NỔI TIẾNG / GIÁ
 * GET /events/recommendations?city=...&target_date=...&lat=...&lng=...&...
 **/
export async function getEventRecommendations(params = {}) {
  const {
    city,
    target_date,
    session,
    lat,
    lng,
    max_distance_km,
  } = params;

  if (!city || !target_date) {
    throw new Error(
      "city và target_date là bắt buộc khi gọi getEventRecommendations()"
    );
  }

  const queryObj = {
    city,
    target_date,
  };

  if (session) queryObj.session = session;
  if (lat != null) queryObj.lat = String(lat);
  if (lng != null) queryObj.lng = String(lng);
  if (max_distance_km != null) queryObj.max_distance_km = String(max_distance_km);

  const query = new URLSearchParams(queryObj).toString();
  const path = `/events/recommendations?${query}`;

  const result = await request(path, "GET");
   const recs = Array.isArray(result.data) ? result.data : [];
  console.log("[recs] parsed array length =", recs.length);

  return recs;
}


/**
 * CHI TIẾT 1 SỰ KIỆN
 * GET /events/{event_id}
 * @param {number|string} eventId
 * @returns {Promise<Object>} EventOut (result.data)
 */
export async function getEventDetail(eventId) {
  if (eventId == null) {
    throw new Error("eventId là bắt buộc khi gọi getEventDetail()");
  }

  const result = await request(`/events/detail/${eventId}`, "GET");
  return result.data;
}


