// fe/js/pages/event.js
// Controller chính cho trang Lễ hội:
// - Bắt event form tìm kiếm
// - Gọi API events
// - Điều khiển các view: bookView, listView, detailView

// Import các hàm gọi API BE cho sự kiện
import {
  listEvents,              // gọi GET /events/list_event (hoặc /events) – lấy danh sách sự kiện
  searchEventByName,       // gọi GET /events/search-by-name – tìm theo tên
  getEventDetail,          // gọi GET /events/{id} – chi tiết 1 sự kiện
  getEventRecommendations, // gọi GET /events/recommendations – gợi ý theo khoảng cách
} from "../api/eventApi.js";

// Import các hàm liên quan đến UI "quyển sách" (trang trái/phải, flip...)
import { initBookView, enterBookMode, enterListMode } from "../ui/bookView.js";

// Import các hàm liên quan tới UI chi tiết + toast
import {
  initDetailView,    // khởi tạo overlay chi tiết (gắn nút close, v.v.)
  showToast,         // hiển thị thông báo nhỏ (toast)
  showEventDetail,   // render chi tiết 1 event (từ API)
  showBookEventDetail, // render chi tiết 1 event tĩnh trong book (Tết, Trung Thu,…)
} from "../ui/detailView.js";

// Import hàm render list kết quả tìm kiếm
import { initListView, renderSearchResults } from "../ui/listView.js";

// Import service giữ state & constant dùng chung cho event
import {
  currentEventSearchConfig, // object: { city, target_date, session }
  updateEventSearchConfig,  // hàm cập nhật currentEventSearchConfig
  updateEventSort,          // hàm update currentEventSort
  resetEventFilters,        // hàm reset bộ lọc (sort, v.v.)
} from "../services/event_service.js";

// ===== STATE TRONG TRANG =====
let searchResults = [];        // danh sách event hiện tại (dạng array EventOut lấy từ BE)
let filterPanel = null;        // DOM element của panel filter (ô lọc)
let eventListContainer = null; // DOM element chứa danh sách kết quả tìm kiếm

// =========================
// GPS
// =========================
export function getUserLocation() {
  // Wrap geolocation trong Promise để dùng với async/await
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      // Trình duyệt không hỗ trợ geolocation
      reject(new Error("Trình duyệt không hỗ trợ định vị GPS."));
      return;
    }

    // Lấy vị trí hiện tại của user
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        // Thành công: trả ra lat/lng
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
      },
      (err) => {
        // Lỗi (user từ chối, hết thời gian, v.v.)
        reject(err);
      },
      {
        enableHighAccuracy: true, // ưu tiên độ chính xác cao
        timeout: 10000,           // tối đa 10s
      }
    );
  });
}

// =========================
// HANDLERS CHÍNH
// =========================

// Submit form (city + date)
async function onSearchSubmit(e) {
  e.preventDefault(); // Ngăn browser reload trang khi submit form

  const cityInput = document.getElementById("city-input");
  const dateInput = document.getElementById("target-date-input");

  // Lấy value từ input, dùng ?. để tránh null, trim() bỏ khoảng trắng thừa
  const city = cityInput?.value?.trim();
  const target_date = dateInput?.value?.trim();

  // Nếu thiếu city hoặc date thì cảnh báo
  if (!city || !target_date) {
    showToast("Vui lòng nhập thành phố và ngày.");
    return;
  }

  // Cập nhật state search hiện tại vào service
  updateEventSearchConfig({
    city,
    target_date,
    session: null, // hiện tại bạn không dùng session nên để null
  });

  try {
    // Gọi API lấy danh sách event theo city + date
    const data = await listEvents({
      city,
      target_date,
      session: null,
    });

    // Lưu kết quả vào state
    searchResults = data || [];

    // Chuyển sang chế độ LIST (ẩn sách, hiện list)
    enterListMode();

    // Render list kết quả, truyền callback:
    // - onRowClick: click vào 1 event thì mở chi tiết
    // - onBackToBook: click nút "Quay lại sách"
    renderSearchResults(searchResults, {
      onRowClick: handleOpenEventDetail,
      onBackToBook: handleBackToBook,
    });
  } catch (err) {
    console.error(err);

    searchResults = [];

    enterListMode();
    renderSearchResults([], {
      onRowClick: handleOpenEventDetail,
      onBackToBook: handleBackToBook,
    });
  }
}

// Gõ Enter trong ô "Tìm kiếm sự kiện..."
async function onKeywordEnter(e) {
  if (e.key !== "Enter") return; // chỉ xử lý khi nhấn Enter
  e.preventDefault();

  const keyword = e.target.value.trim();
  if (!keyword) {
    // Nếu keyword rỗng: xóa list & quay lại sách
    if (eventListContainer) eventListContainer.innerHTML = "";
    handleBackToBook();
    return;
  }

  try {
    // Gọi API tìm kiếm theo tên
    const results = await searchEventByName(keyword, 10);
    searchResults = results || [];

    enterListMode();
    renderSearchResults(searchResults, {
      onRowClick: handleOpenEventDetail,
      onBackToBook: handleBackToBook,
    });
  } catch (err) {
    console.error("Lỗi tìm kiếm theo tên:", err);
    searchResults = [];
    enterListMode();
    renderSearchResults([], {
      onRowClick: handleOpenEventDetail,
      onBackToBook: handleBackToBook,
    });
  }
}

// Mở chi tiết event động (gọi API /events/{id})
async function handleOpenEventDetail(eventId) {
  try {
    // Gọi API lấy chi tiết event theo id
    const data = await getEventDetail(eventId);
    // Hiển thị overlay chi tiết
    showEventDetail(data);
  } catch (err) {
    console.error("Lỗi load chi tiết:", err);
    showToast("Có lỗi xảy ra khi tải chi tiết lễ hội.");
  }
}

// Mở chi tiết cho event tĩnh trong “quyển sách” (Tết, Trung Thu,…)
function handleOpenBookEventDetail(bookEvent) {
  // Chỉ gọi hàm render chi tiết cho dữ liệu bookEvents (tĩnh)
  showBookEventDetail(bookEvent);
}

// Quay lại chế độ “sách”
function handleBackToBook() {
  if (eventListContainer) {
    // Xóa nội dung list
    eventListContainer.innerHTML = "";
  }
  // Hiện lại UI sách, ẩn list
  enterBookMode();
}

// =========================
// SẮP XẾP / LỌC
// =========================

async function applySort(sortValue) {
  // Cập nhật sort trong service (nếu bạn muốn dùng ở chỗ khác)
  console.log("[applySort] sortValue =", sortValue);  // <<< THÊM

  updateEventSort(sortValue);

  // Chưa có search city/date thì không filter được
  if (!currentEventSearchConfig.city || !currentEventSearchConfig.target_date) {
    showToast("Hãy tìm lễ hội trước rồi mới dùng bộ lọc.");
    return;
  }

  // Không chọn sort -> load lại list mặc định (không sort, không distance)
  if (!sortValue) {
    try {
      const data = await listEvents({
        city: currentEventSearchConfig.city,
        target_date: currentEventSearchConfig.target_date,
        session: currentEventSearchConfig.session,
      });
      searchResults = data || [];
      enterListMode();
      renderSearchResults(searchResults, {
        onRowClick: handleOpenEventDetail,
        onBackToBook: handleBackToBook,
      });
    } catch (err) {
      console.error(err);
      showToast("Không thể tải danh sách.");
    }
    return;
  }

  // 1) GIÁ / ĐỘ NỔI TIẾNG -> gọi listEvents với sort
  if (
    sortValue === "price_asc" ||
    sortValue === "price_desc" ||
    sortValue === "popularity_desc" //||
    //sortValue === "distance_asc"
  ) {
    try {
      const data = await listEvents({
        city: currentEventSearchConfig.city,
        target_date: currentEventSearchConfig.target_date,
        session: currentEventSearchConfig.session,
        sort: sortValue, // sort dựa trên price/popularity
      });
      searchResults = data || [];
      enterListMode();
      renderSearchResults(searchResults, {
        onRowClick: handleOpenEventDetail,
        onBackToBook: handleBackToBook,
      });
    } catch (err) {
      console.error(err);
      showToast("Không thể sắp xếp theo bộ lọc đã chọn.");
    }
    return;
  }

  // 2) KHOẢNG CÁCH -> gọi /events/recommendations
  if (sortValue === "distance_asc") {
    try {
      // Lấy vị trí hiện tại của user
      const { lat, lng } = await getUserLocation();

      // Checkbox "Chỉ hiển thị trong bán kính 5km"
      const onlyWithin5 =
        document.getElementById("filter-distance-5km")?.checked || false;

      // Chuẩn bị params gọi API
      const params = {
        city: currentEventSearchConfig.city,
        target_date: currentEventSearchConfig.target_date,
        session: currentEventSearchConfig.session,
        lat,
        lng,
      };
      if (onlyWithin5) {
        params.max_distance_km = 5;
      }

      // Gọi BE gợi ý theo khoảng cách
      const recs = await getEventRecommendations(params);
      searchResults = recs || [];
      enterListMode();
      renderSearchResults(searchResults, {
        onRowClick: handleOpenEventDetail,
        onBackToBook: handleBackToBook,
      });
    } catch (err) {
  console.error("Không thể lọc theo khoảng cách:", err);

  // Nếu là lỗi lấy vị trí (navigator.geolocation)
  if (err && err.code !== undefined && err.message) {
    showToast("Không lấy được vị trí (bị chặn GPS hoặc lỗi trình duyệt).");
  } else {
    // Còn lại là lỗi từ server / API
    showToast("Server lọc theo khoảng cách đang lỗi (HTTP 4xx/5xx).");
  }

  enterListMode();
  renderSearchResults(searchResults, {
    onRowClick: handleOpenEventDetail,
    onBackToBook: handleBackToBook,
      });
    }
    return;
  }

  // sortValue lạ -> giữ nguyên list hiện tại
  enterListMode();
  renderSearchResults(searchResults, {
    onRowClick: handleOpenEventDetail,
    onBackToBook: handleBackToBook,
  });
}

// =========================
// FILTER PANEL
// =========================

function initFilterPanel() {
  const filterBtn = document.getElementById("filter-btn");
  filterPanel = document.getElementById("filter-panel");
  const applyFilterBtn = document.getElementById("filter-apply-btn");
  const resetFilterBtn = document.getElementById("filter-reset-btn");

  // Nút mở/đóng panel lọc (icon cái phễu trên navbar)
  if (filterBtn && filterPanel) {
    filterBtn.addEventListener("click", () => {
      filterPanel.classList.toggle("hidden");
    });
  }

  // Nút "Áp dụng"
  if (applyFilterBtn && filterPanel) {
    applyFilterBtn.addEventListener("click", () => {
      // Lấy sort được chọn (radio)
      const selected = filterPanel.querySelector('input[name="sort"]:checked');
      const sortValue = selected ? selected.value : null;

      console.log("[Filter] sortValue selected =", sortValue);  // <= THÊM

      // Gọi applySort để xử lý logic
      applySort(sortValue);

      // Ẩn panel sau khi áp dụng
      filterPanel.classList.add("hidden");
    });
  }

  // Nút "Bỏ lọc"
  if (resetFilterBtn && filterPanel) {
    resetFilterBtn.addEventListener("click", async () => {
      // Reset state filter trong service
      resetEventFilters();
      updateEventSort(null);

      // Bỏ chọn tất cả radio sort
      filterPanel
        .querySelectorAll('input[name="sort"]')
        .forEach((i) => (i.checked = false));

      // Bỏ check checkbox bán kính 5km
      const distanceCheckbox = document.getElementById("filter-distance-5km");
      if (distanceCheckbox) distanceCheckbox.checked = false;

      // Nếu chưa search city/date thì báo và không làm gì thêm
      if (
        !currentEventSearchConfig.city ||
        !currentEventSearchConfig.target_date
      ) {
        showToast("Chưa có kết quả để bỏ lọc. Hãy tìm lễ hội trước.");
        return;
      }

      try {
        // Gọi lại listEvents với điều kiện cũ nhưng không sort
        const data = await listEvents({
          city: currentEventSearchConfig.city,
          target_date: currentEventSearchConfig.target_date,
          session: currentEventSearchConfig.session,
        });
        searchResults = data || [];
        enterListMode();
        renderSearchResults(searchResults, {
          onRowClick: handleOpenEventDetail,
          onBackToBook: handleBackToBook,
        });
      } catch (err) {
        console.error(err);
        showToast("Không thể tải lại danh sách.");
      }
    });
  }
}

// =========================
// MAIN INIT
// =========================

function initEventPage() {
  // Khởi tạo icon lucide (nếu thư viện đã load)
  if (window.lucide) lucide.createIcons();

  // Lấy container list từ DOM
  eventListContainer = document.getElementById("event-list-container");

  // Khởi tạo các view con:
  initDetailView(); // overlay chi tiết
  initListView();   // (nếu bạn có logic setup listView riêng)
  initBookView({ onBookDetailClick: handleOpenBookEventDetail }); // setup book + callback nút "Xem chi tiết" trong sách

  // Mặc định: chế độ SÁCH (book mode)
  enterBookMode();

  // Form & inputs
  const form = document.getElementById("event-search-form");
  if (form) {
    form.addEventListener("submit", onSearchSubmit);
  }

  const keywordInput = document.getElementById("keyword-input");
  if (keywordInput) {
    keywordInput.addEventListener("keydown", onKeywordEnter);
  }

  // Panel lọc
  initFilterPanel();
}

// Khi DOM load xong thì khởi chạy trang
document.addEventListener("DOMContentLoaded", () => {
  initEventPage();

  // Xử lý nút quay về trang chính
  const backBtn = document.getElementById("back-btn");
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      window.location.href = "main.html";
    });
  }
});
