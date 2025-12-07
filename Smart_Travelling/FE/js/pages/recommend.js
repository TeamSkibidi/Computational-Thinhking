// FE/js/pages/recommend.js
// Logic recommend: gọi API, quản lý seen_ids, render bằng <template>

import { recommendPlaces } from "../api/visitorApi.js";

// ------- DOM -------
const cityInput = document.getElementById("cityInput");
const recommendBtn = document.getElementById("recommendBtn");
const resetSeenBtn = document.getElementById("resetSeenBtn");
const backToHomeBtn = document.getElementById("backToHomeBtn");

const placesContainer = document.getElementById("placesContainer");
const emptyMessage = document.getElementById("emptyMessage");
const statusMessage = document.getElementById("statusMessage");
const loadingOverlay = document.getElementById("loadingOverlay");
const placeCardTemplate = document.getElementById("placeCardTemplate");

// ------- LocalStorage helpers -------

function getSeenKey(city) {
  return `visitor_seen_ids_${city.trim().toLowerCase()}`;
}

function loadSeenIds(city) {
  const key = getSeenKey(city);
  const raw = localStorage.getItem(key);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveSeenIds(city, ids) {
  const key = getSeenKey(city);
  localStorage.setItem(key, JSON.stringify(ids));
}

function clearSeenIds(city) {
  const key = getSeenKey(city);
  localStorage.removeItem(key);
}

// ------- UI helpers -------

function setStatus(text, type = "") {
  statusMessage.textContent = text || "";
  statusMessage.classList.remove("error", "success");
  if (type) statusMessage.classList.add(type);
}

function showLoading(show) {
  loadingOverlay.classList.toggle("hidden", !show);
}

function clearPlaces() {
  placesContainer.innerHTML = "";
}

// Tạo card từ template, gán dữ liệu vào
function createPlaceCard(place) {
  // Clone template
  const fragment = placeCardTemplate.content.cloneNode(true);

  const nameEl = fragment.querySelector(".js-place-name");
  const idEl = fragment.querySelector(".js-place-id");
  const summaryEl = fragment.querySelector(".js-place-summary");

  const metaRating = fragment.querySelector(".js-meta-rating");
  const ratingValueEl = fragment.querySelector(".js-rating-value");
  const reviewCountEl = fragment.querySelector(".js-review-count");

  const metaPrice = fragment.querySelector(".js-meta-price");
  const priceValueEl = fragment.querySelector(".js-price-value");

  const metaTime = fragment.querySelector(".js-meta-time");
  const timeRangeEl = fragment.querySelector(".js-time-range");

  const metaPopularity = fragment.querySelector(".js-meta-popularity");
  const popularityValueEl = fragment.querySelector(".js-popularity-value");

  const tagsContainer = fragment.querySelector(".js-place-tags");
  const addressEl = fragment.querySelector(".js-place-address");

  // Dữ liệu cơ bản
  const name = place.name || "Địa điểm không tên";
  const summary = place.summary || place.description || "Chưa có mô tả.";

  nameEl.textContent = name;
  idEl.textContent = place.id != null ? `#${place.id}` : "#?"; 
  summaryEl.textContent = summary;

  // Rating
  const rating = place.rating ?? null;
  const reviewCount = place.reviewCount ?? 0;
  if (rating !== null) {
    metaRating.classList.remove("hidden");
    ratingValueEl.textContent = rating.toFixed(1);
    reviewCountEl.textContent = ` · ${reviewCount} đánh giá`;
  } else {
    metaRating.classList.add("hidden");
  }

  // Price
  const price = place.priceVND ?? null;
  if (price !== null) {
    metaPrice.classList.remove("hidden");
    priceValueEl.textContent = `${price.toLocaleString("vi-VN")} VND`;
  } else {
    metaPrice.classList.add("hidden");
  }

  // Time
  const openTime = place.openTime || "";
  const closeTime = place.closeTime || "";
  if (openTime || closeTime) {
    metaTime.classList.remove("hidden");
    timeRangeEl.textContent = `${openTime || "?"} - ${closeTime || "?"}`;
  } else {
    metaTime.classList.add("hidden");
  }

  // Popularity
  const popularity = place.popularity ?? null;
  if (popularity !== null) {
    metaPopularity.classList.remove("hidden");
    popularityValueEl.textContent = popularity;
  } else {
    metaPopularity.classList.add("hidden");
  }

  // Tags
  tagsContainer.innerHTML = "";
  const tags = Array.isArray(place.tags) ? place.tags.slice(0, 4) : [];
  if (tags.length > 0) {
    tags.forEach((tag) => {
      const span = document.createElement("span");
      span.className = "tag";
      span.textContent = tag;
      tagsContainer.appendChild(span);
    });
  }

  // Address
  let addressText = "";
  if (place.address) {
    const a = place.address;
    const parts = [
      a.houseNumber,
      a.street,
      a.ward,
      a.district,
      a.city,
    ].filter(Boolean);
    addressText = parts.join(", ");
  }

  if (addressText) {
    addressEl.textContent = `📍 ${addressText}`;
    addressEl.classList.remove("hidden");
  } else {
    addressEl.textContent = "";
    addressEl.classList.add("hidden");
  }

  return fragment;
}

// Render list địa điểm
function renderPlaces(list) {
  clearPlaces();

  if (!list || list.length === 0) {
    emptyMessage.classList.remove("hidden");
    return;
  }

  emptyMessage.classList.add("hidden");

  list.forEach((place) => {
    const cardFragment = createPlaceCard(place);
    placesContainer.appendChild(cardFragment);
  });
}

// ------- Main logic -------

let userId = null;

async function handleRecommendClick() {
  const city = cityInput.value.trim();
  if (!city) {
    alert("Vui lòng nhập tên thành phố trước!");
    cityInput.focus();
    return;
  }

  showLoading(true);
  setStatus("");

  try {
    const currentSeen = loadSeenIds(city);

    const data = await recommendPlaces(city, currentSeen, 5, userId);
    // data: { city, places, seen_ids }

    renderPlaces(data.places);
    saveSeenIds(city, data.seen_ids || []);

    if (!data.places || data.places.length === 0) {
      setStatus("Không tìm thấy địa điểm nào cho thành phố này.", "error");
    } else {
      setStatus(
        `Đã gợi ý ${data.places.length} địa điểm cho thành phố ${data.city}.`,
        "success"
      );
    }
  } catch (err) {
    console.error(err);
    setStatus("Lỗi khi gợi ý địa điểm: " + err.message, "error");
  } finally {
    showLoading(false);
  }
}

function handleResetSeen() {
  const city = cityInput.value.trim();
  if (!city) {
    alert("Nhập thành phố rồi hãy xóa lịch sử gợi ý nhé.");
    cityInput.focus();
    return;
  }

  if (confirm(`Xóa lịch sử gợi ý cho thành phố "${city}"?`)) {
    clearSeenIds(city);
    setStatus("Đã xóa lịch sử gợi ý cho thành phố này.", "success");
  }
}

// ------- Events -------

recommendBtn.addEventListener("click", handleRecommendClick);

cityInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleRecommendClick();
  }
});

resetSeenBtn.addEventListener("click", handleResetSeen);

backToHomeBtn.addEventListener("click", () => {
  // chỉnh lại đường dẫn nếu trang main của bạn khác
  window.location.href = "../html/main.html";
});

// SỬA: Init khi DOM load xong
document.addEventListener("DOMContentLoaded", () => {
  // Lấy user từ localStorage
  const savedUser = localStorage.getItem("user");
  if (savedUser) {
    const user = JSON.parse(savedUser);
    userId = user.id;  // ← Lưu user_id
    console.log("User ID:", userId);  // Debug
  }
  
  renderPlaces([]);
  setStatus('Nhập thành phố và nhấn "Gợi ý 5 địa điểm" để bắt đầu.');
});
