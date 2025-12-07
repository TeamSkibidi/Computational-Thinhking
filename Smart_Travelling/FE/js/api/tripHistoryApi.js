import { request } from "./request.js";

export async function getTripHistory(userId) {
  const res = await request(`/recommand/history/${userId}`, "GET");
  return res.data;
}

export async function getTripDetail(tripId, userId) {
  const res = await request(`/recommand/history/${userId}/${tripId}`, "GET");
  return res.data;
}

export async function deleteTrip(tripId, userId) {
  const res = await request(`/recommand/history/${userId}/${tripId}`, "DELETE");
  return res;
}

export async function deleteAllTrips(userId) {
  const res = await request(`/recommand/history/${userId}`, "DELETE");
  return res;
}