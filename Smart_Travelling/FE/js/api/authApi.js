// chứa request đăng kí và đăng nhập

import { request } from "./request.js";

// đăng kí POST/auth/register
export function register(username, password) {
    // body phải đúng key backend cần
    const body = { username, password };

    // gọi request chung
    return request("/auth/register", "POST", body);
}

//đăng nhập POST/auth/login
export function login(username, password) {
  const body = { username, password };
  return request("/auth/login", "POST", body);
}