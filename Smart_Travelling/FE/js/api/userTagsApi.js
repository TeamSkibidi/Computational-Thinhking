import { request } from "./request.js";


/**
 * CẬP NHẬT TAGS
 * POST /users/{user_id}/tags
 */
export async function updateUserTags(userId, tags) {
  const result = await request(`/users/${userId}/tags`, "POST", { tags });
  return result;
}