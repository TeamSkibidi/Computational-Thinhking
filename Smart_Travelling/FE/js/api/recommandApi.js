import { request } from './request.js';

// gợi ý chuyến đi POST /recommand/trip
export async function tripRecommand(data) {
    return request("/recommand/trip", "POST", data);
}