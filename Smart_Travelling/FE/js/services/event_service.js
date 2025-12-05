// js/services/event_service.js
// Service cho trang sự kiện: giữ state & constant, không động tới DOM

// Các loại sort cho event (giá, nổi tiếng, khoảng cách)
export const EVENT_SORT_OPTIONS = {
  NONE: null,
  PRICE_ASC: "price_asc",
  PRICE_DESC: "price_desc",
  POPULARITY_DESC: "popularity_desc",
  DISTANCE_ASC: "distance_asc",
};

// Điều kiện tìm kiếm hiện tại (city/date/session)
export let currentEventSearchConfig = {
  city: "",
  target_date: "",
  session: null,
};

// Sort hiện tại đang áp dụng
let currentEventSort = EVENT_SORT_OPTIONS.NONE;

/**
 * Cập nhật điều kiện search (city, target_date, session)
 * patch chỉ cần truyền những field muốn đổi
 */
export function updateEventSearchConfig(patch) {
  currentEventSearchConfig = {
    ...currentEventSearchConfig,
    ...patch,
  };
}

/**
 * Cập nhật sort hiện tại
 */
export function updateEventSort(newSort) {
  currentEventSort = newSort ?? EVENT_SORT_OPTIONS.NONE;
}

/**
 * Reset tất cả filter/sort về mặc định
 */
export function resetEventFilters() {
  currentEventSort = EVENT_SORT_OPTIONS.NONE;
}
