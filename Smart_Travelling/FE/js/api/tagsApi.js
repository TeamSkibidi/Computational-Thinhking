import { request } from "./request.js";

export async function getTags( ) {
  const result = await request(`/tags/items`, "GET");
  return result; 
}