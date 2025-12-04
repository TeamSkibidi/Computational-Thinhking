import { request } from "./request.js"


/**
 * TÌM KIẾM LỄ HỘI THEO TÊN
 * GET /events/search-by-name?keyword=...
 *
 * @param {string} keyword - Tên lễ hội người dùng gõ (có dấu hoặc không dấu)
 * @param {number} limit - Số kết quả tối đa muốn lấy (mặc định 5)
 * @returns {Promise<Array>} Mảng EventOut từ backend
 */
export async function searchEventByName(keyword, limit = 5) {
  const query = new URLSearchParams({ keyword, limit }).toString();
  const result = await request(`/events/search-by-name?${query}`, "GET");
  return result.data; // backend trả { status, data }, mình lấy data = list events
}


/**
 * LẤY DANH SÁCH SỰ KIỆN
 * GET /events?city=...&target_date=...&session=...
 *
 * @param {object} params
 *   {
 *     city: string,          // bắt buộc
 *     target_date: string,   // bắt buộc, format "YYYY-MM-DD"
 *   }
 * @returns {Promise<Array>} Mảng EventOut từ backend
 */

export async function listEvents(params = {}){
    const {city, target_date} = params;

    // 2 field này BE đang để bắt buộc
    if (!city || !target_date){
        throw new Error ("city and target_date are compulsory ")
    }

    const queryObj = {city, target_date};
    const query = new URLSearchParams(queryObj).toString();
    const path = `/events?${query}`;

    // BE tra ve truc tiep EventOut
    const events = await request(path, "GET");
    return events;
}

/**
 * CHI TIẾT 1 SỰ KIỆN
 * GET /events/{event_id}
 *
 * @param {number|string} eventId
 * @returns {Promise<Object>} EventOut từ backend
 */

export async function getEventDetail (event_id){
    if (event_id === null || event_id === null ){
        throw new Error("event_id is compulsory for calling getEventDetail()")
    }
    const event = await request(`/events/${eventId}`, "GET");
    return event;
}

/**
 * GỢI Ý SỰ KIỆN THEO KHOẢNG CÁCH / GIÁ / ĐỘ NỔI TIẾNG
 * GET /events/recommendations?city=...&target_date=...&...
 *
 * @param {object} params
 *   {
 *     city: string,              // bắt buộc
 *     target_date: string,       // bắt buộc, "YYYY-MM-DD"
 *     session?: string,
 *     price?: number,
 *     lat?: number,
 *     lng?: number,
 *     max_distance_km?: number,
 *   }
 * @returns {Promise<Array>} Mảng EventOut từ backend
 */
export async function getEventRecommendations(params = {}){
    const {
        city,
        target_date,
        session,
        price,
        lat,
        lng,
        max_distance_km,
    } = params;

    if (!city || !target_date){
        throw new Error ("city and target_date are compulsory for calling getEventRecommendation()");
    }

    const queryObj = { city, target_date };

    if (session) queryObj.session = session;
    if (price !== null && price !== null) queryObj.price = String(price);
    if (lat !== null && lat !== null) queryObj.lat = String(lat);
    if (lng !== null && lng !== null) queryObj.lng = String(lng);
    if (max_distance_km != null) queryObj.max_distance_km = max_distance_km;


    const query = new URLSearchParams(queryObj).toString();
    const path = `/events/recommendations?${query}`;

    const events = await request(path, "GET");
    return events;
}