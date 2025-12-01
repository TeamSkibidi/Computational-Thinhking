// =========================
// 1) IMPORT API TỪ eventApi.js
// =========================

import {
  listEvents,
  searchEventByName,
  getEventDetail,
  getEventRecommendations,
} from "../api/eventApi.js";


// =========================
// 2) DATA CỐ ĐỊNH DÙNG CHO QUYỂN SÁCH
// =========================

const bookEvents = [
  {
    id: 1,
    name: "Tết Nguyên Đán",
    date: "01 - 03 Tháng 1 (Âm Lịch)",
    loc: "Toàn Quốc",
    theme: "theme-tet",
    img: "../images/Tết.jpg",
    desc: "Chào đón năm mới...",
    tags: ["Truyền thống", "Gia đình"],
    particle: "🌸",
  },
  {
    id: 2,
    name: "Tết Trung Thu",
    date: "15 Tháng 8 (Âm Lịch)",
    loc: "Toàn Quốc",
    theme: "theme-trungthu",
    img: "../images/Trung_Thu.jpg",
    desc: "Đêm hội trăng rằm...",
    tags: ["Trẻ em", "Văn hóa"],
    particle: "⭐",
  },
];


// =========================
// 3) DATA ĐỘNG DÙNG CHO LIST (kết quả tìm kiếm)
// =========================

let searchResults = [];   // mảng event từ API
let currentSort = null;

// sách đang active hay đang xem list
let isBookMode = true;
let flipIntervalId = null; // giữ id setInterval để lật sách

// nhớ lại điều kiện tìm kiếm gần nhất (để filter dùng lại)
let lastSearchParams = {
  city: null,
  target_date: null,
  session: null,
};


// =========================
// 4) STATE CHO SÁCH
// =========================

let currentIndex = 0;     // event đang hiển thị trong bookEvents
let isAnimating = false;  // tránh lật trùng


// =========================
// 5) LẤY CÁC PHẦN TỬ DOM
// =========================

let bookWrapper;
let staticLeft;
let staticRight;

let eventListContainer = null;
let highlightContainer = null;

// overlay chi tiết
let eventDetailOverlay = null;
let eventDetailContent = null;

// thông báo nhỏ (toast)
let toastEl = null;
let toastTimeoutId = null;


// Bật chế độ SÁCH: hiện sách, ẩn list
function enterBookMode() {
  isBookMode = true;
  if (bookWrapper) {
    bookWrapper.classList.remove("show-list");
  }
  if (eventListContainer) {
    eventListContainer.style.display = "none";
  }
}

// Bật chế độ LIST: ẩn sách, hiện list
function enterListMode() {
  isBookMode = false;
  if (bookWrapper) {
    bookWrapper.classList.add("show-list");
  }
  if (eventListContainer) {
    eventListContainer.style.display = "block";
  }
}


// =========================
// 6) FORMAT NGÀY
// =========================

function formatFullDate(isoString) {
  if (!isoString) return "Không rõ";
  const d = new Date(isoString);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}

function formatDateRange(startIso, endIso) {
  if (!startIso && !endIso) return "Không rõ";
  if (startIso && !endIso) return formatFullDate(startIso);
  if (!startIso && endIso) return formatFullDate(endIso);

  const start = new Date(startIso);
  const end = new Date(endIso);

  const sd = String(start.getDate()).padStart(2, "0");
  const sm = String(start.getMonth() + 1).padStart(2, "0");
  const sy = start.getFullYear();

  const ed = String(end.getDate()).padStart(2, "0");
  const em = String(end.getMonth() + 1).padStart(2, "0");
  const ey = end.getFullYear();

  if (sy === ey) {
    if (sd === ed && sm === em) {
      return `${sd}/${sm}/${sy}`;
    }
    return `${sd}/${sm}/${sy} - ${ed}/${em}/${ey}`;
  }
  return `${sd}/${sm}/${sy} - ${ed}/${em}/${ey}`;
}


// =========================
// TOAST (CẢNH BÁO NHỎ TRONG WEB)
// =========================

function showToast(message) {
  if (!toastEl) return;

  if (toastTimeoutId) {
    clearTimeout(toastTimeoutId);
    toastTimeoutId = null;
  }

  toastEl.textContent = message;
  toastEl.classList.add("show");

  toastTimeoutId = setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}


// =========================
// CHI TIẾT LỄ HỘI (OVERLAY)
// =========================

function buildEventDetailHTML(e) {
  const imgUrl = e.image_url || "../images/Trung_Thu.jpg";
  const cityRegion = e.region ? `${e.city}, ${e.region}` : e.city || "Không rõ";
  const timeRange = formatDateRange(e.start_datetime, e.end_datetime);
  const price = e.price_vnd || "Không rõ";
  const popularity =
    e.popularity != null ? e.popularity.toFixed(1) : "Không rõ";
  const distance =
    e.distance_km != null ? `${Number(e.distance_km).toFixed(1)} km` : "Không rõ";
  const activities = Array.isArray(e.activities) ? e.activities : [];

  return `
    <div class="event-detail-body">
      <div class="event-detail-image" style="background-image:url('${imgUrl}')"></div>
      <div class="event-detail-info">
        <div class="event-detail-title">${e.name}</div>
        <div class="event-detail-meta">${cityRegion}</div>
        <div class="event-detail-meta">Thời gian: ${timeRange}</div>

        <div class="event-detail-summary">
          ${e.summary || ""}
        </div>

        <div class="event-detail-tags">
          ${activities.map((a) => `<span class="event-detail-tag">${a}</span>`).join("")}
        </div>

        <div class="event-detail-fields">
          <div class="event-detail-field">
            <span class="event-detail-label">Giá vé:</span> ${price}
          </div>
          <div class="event-detail-field">
            <span class="event-detail-label">Độ nổi tiếng:</span> ${popularity}
          </div>
          <div class="event-detail-field">
            <span class="event-detail-label">Khoảng cách:</span> ${distance}
          </div>
        </div>
      </div>
    </div>
  `;
}

async function openEventDetail(eventId) {
  if (!eventDetailOverlay || !eventDetailContent) return;
  if (eventId == null) return;

  eventDetailOverlay.classList.add("show");
  eventDetailContent.innerHTML =
    `<div style="padding:24px;font-size:14px;">Đang tải chi tiết lễ hội...</div>`;

  try {
    const data = await getEventDetail(eventId);
    eventDetailContent.innerHTML = buildEventDetailHTML(data);
    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Lỗi load chi tiết:", err);
    eventDetailContent.innerHTML =
      `<div style="padding:24px;font-size:14px;color:#b91c1c;">
        Có lỗi xảy ra khi tải chi tiết lễ hội.
      </div>`;
  }
}

function closeEventDetail() {
  if (!eventDetailOverlay) return;
  eventDetailOverlay.classList.remove("show");
}


// =========================
// 7. HELPER RENDER HÌNH ẢNH (TRANG TRÁI)
// =========================

function getImageHTML(data) {
  return `
    <div class="image-container" style="background-image: url('${data.img}')">
      <div class="image-overlay">
        <div class="text-sm font-bold tracking-widest uppercase opacity-80 mb-2">${data.loc}</div>
        <div class="text-3xl font-serif flex items-center gap-2">
          <i data-lucide="calendar"></i> ${data.date}
        </div>
      </div>
    </div>
  `;
}


// =========================
// 8. HELPER RENDER NỘI DUNG (TRANG PHẢI)
// =========================

function getTextHTML(data) {
  return `
    <div class="text-container ${data.theme}">
      <div class="flex gap-2 mb-4">
        ${
          (data.tags || [])
            .map(
              (t) =>
                `<span class="px-3 py-1 bg-black/5 rounded text-xs font-bold uppercase text-[var(--theme-primary)] border border-[var(--theme-primary)]/20">${t}</span>`
            )
            .join("")
        }
      </div>
      <h1 class="text-5xl font-bold mb-6 text-[var(--theme-primary)] leading-tight">${data.name}</h1>
      <p class="text-lg leading-loose text-gray-700 text-justify">${data.desc}</p>
      <div class="mt-8">
        <button class="px-6 py-3 bg-[var(--theme-primary)] text-white rounded shadow-lg hover:shadow-xl transition transform hover:-translate-y-1 flex items-center gap-2">
          Xem chi tiết <i data-lucide="arrow-right" width="16"></i>
        </button>
      </div>
    </div>
  `;
}


// =========================
// 9. ĐỔI THEME CHO BODY
// =========================

function updateBodyTheme(themeClass) {
  document.body.className = themeClass;
}


// =========================
// 10. RENDER 2 TRANG TĨNH
// =========================

function renderStaticPage(leftIndex, rightIndex) {
  staticLeft.innerHTML  = getImageHTML(bookEvents[leftIndex]);
  staticRight.innerHTML = getTextHTML(bookEvents[rightIndex]);

  staticLeft.className  = `static-page static-left ${bookEvents[leftIndex].theme}`;
  staticRight.className = `static-page static-right ${bookEvents[rightIndex].theme}`;
}


// =========================
// 11. HIỆU ỨNG PARTICLE
// =========================

function startParticles(char) {
  document.querySelectorAll(".particle").forEach((el) => el.remove());

  for (let i = 0; i < 10; i++) {
    setTimeout(() => {
      const p = document.createElement("div");
      p.className = "particle";
      p.innerText = char;

      p.style.left = Math.random() * 100 + "vw";
      p.style.top = "-50px";
      p.style.fontSize = Math.random() * 20 + 10 + "px";
      p.style.animationDuration = Math.random() * 3 + 5 + "s";

      document.body.appendChild(p);
    }, i * 400);
  }
}


// =========================
// 12. LẬT SANG SỰ KIỆN TIẾP THEO
// =========================

function flipToNext() {
  if (!isBookMode) return;
  if (isAnimating || bookEvents.length === 0) return;
  isAnimating = true;

  const nextIndex   = (currentIndex + 1) % bookEvents.length;
  const currentData = bookEvents[currentIndex];
  const nextData    = bookEvents[nextIndex];

  updateBodyTheme(nextData.theme);

  staticRight.innerHTML = getTextHTML(nextData);
  staticRight.className = `static-page static-right ${nextData.theme}`;

  const flipper = document.createElement("div");
  flipper.className = "flipper is-flipping";

  const front = document.createElement("div");
  front.className = `flipper-face flipper-front ${currentData.theme}`;
  front.innerHTML = getTextHTML(currentData);

  const back = document.createElement("div");
  back.className = `flipper-face flipper-back ${nextData.theme}`;
  back.innerHTML = getImageHTML(nextData);

  flipper.appendChild(front);
  flipper.appendChild(back);
  bookWrapper.appendChild(flipper);

  lucide.createIcons();

  setTimeout(() => startParticles(nextData.particle), 500);

  setTimeout(() => {
    staticLeft.innerHTML = getImageHTML(nextData);
    staticLeft.className = `static-page static-left ${nextData.theme}`;
    flipper.remove();
    currentIndex = nextIndex;
    isAnimating  = false;
    lucide.createIcons();
  }, 2000);
}


// =========================
// 13. HÀM KHỞI TẠO TRANG SÁCH
// =========================

function initBookPage() {
  if (!bookEvents.length) return;

  currentIndex = 0;
  renderStaticPage(currentIndex, currentIndex);

  updateBodyTheme(bookEvents[currentIndex].theme);
  lucide.createIcons();
  startParticles(bookEvents[currentIndex].particle);

  flipIntervalId = setInterval(flipToNext, 5000);
}


// =========================
// 14. ENTRY POINT (DOM loaded)
// =========================

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();

  bookWrapper = document.getElementById("bookWrapper");
  staticLeft  = document.getElementById("staticLeft");
  staticRight = document.getElementById("staticRight");

  toastEl = document.getElementById("event-toast");

  // --- FILTER ---
  const filterBtn = document.getElementById("filter-btn");
  const filterPanel = document.getElementById("filter-panel");
  const applyFilterBtn = document.getElementById("filter-apply-btn");
  const resetFilterBtn = document.getElementById("filter-reset-btn");

  if (filterBtn && filterPanel) {
    filterBtn.addEventListener("click", () => {
      filterPanel.classList.toggle("hidden");
    });
  }

  if (applyFilterBtn && filterPanel) {
    applyFilterBtn.addEventListener("click", () => {
      const selected = filterPanel.querySelector('input[name="sort"]:checked');
      const sortValue = selected ? selected.value : null;
      applySort(sortValue);
      filterPanel.classList.add("hidden");
    });
  }

  if (resetFilterBtn && filterPanel) {
    resetFilterBtn.addEventListener("click", async () => {
      currentSort = null;

      filterPanel
        .querySelectorAll('input[name="sort"]')
        .forEach((i) => (i.checked = false));

      const distanceCheckbox = document.getElementById("filter-distance-5km");
      if (distanceCheckbox) distanceCheckbox.checked = false;

      if (!lastSearchParams.city || !lastSearchParams.target_date) {
        showToast("Chưa có kết quả để bỏ lọc. Hãy tìm lễ hội trước.");
        return;
      }

      try {
        const data = await listEvents({
          city: lastSearchParams.city,
          target_date: lastSearchParams.target_date,
          session: lastSearchParams.session,
        });
        searchResults = data || [];
        renderSearchResults(searchResults);
      } catch (err) {
        console.error(err);
        showToast("Không thể tải lại danh sách.");
      }
    });
  }

  eventListContainer   = document.getElementById("event-list-container");
  highlightContainer   = document.getElementById("highlight-event");
  eventDetailOverlay   = document.getElementById("event-detail-overlay");
  eventDetailContent   = document.getElementById("event-detail-content");

  enterBookMode();

  const closeBtn = document.getElementById("event-detail-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", closeEventDetail);
  }
  if (eventDetailOverlay) {
    eventDetailOverlay.addEventListener("click", (e) => {
      if (e.target === eventDetailOverlay) {
        closeEventDetail();
      }
    });
  }

  initBookPage();

  const form = document.getElementById("event-search-form");
  if (form) {
    form.addEventListener("submit", onSearchSubmit);
  }

  const keywordInput = document.getElementById("keyword-input");
  if (keywordInput) {
    keywordInput.addEventListener("keydown", onKeywordEnter);
  }
});


// =========================
// 15. LOGIC TÌM KIẾM & RENDER LIST
// =========================

async function onSearchSubmit(e) {
  e.preventDefault();

  const city = document.getElementById("city-input").value;
  const target_date = document.getElementById("target-date-input").value;

  if (!city || !target_date) {
    showToast("Vui lòng nhập thành phố và ngày.");
    return;
  }

  lastSearchParams = {
    city,
    target_date,
    session: null,
  };

  try {
    const data = await listEvents({
      city,
      target_date,
      session: null,
    });

    searchResults = data || [];
    renderSearchResults(searchResults);
  } catch (err) {
    console.error(err);
    renderSearchResults([]);
  }
}

async function onKeywordEnter(e) {
  if (e.key !== "Enter") return;
  e.preventDefault();

  const keywordInput = e.target;
  const keyword = keywordInput.value.trim();

  if (!keyword) {
    if (eventListContainer) eventListContainer.innerHTML = "";
    enterBookMode();
    return;
  }

  try {
    const results = await searchEventByName(keyword, 10);
    searchResults = results || [];
    renderSearchResults(searchResults);
  } catch (err) {
    console.error("Lỗi tìm kiếm theo tên:", err);
    renderSearchResults([]);
  }
}


// =========================
// GPS
// =========================

function getUserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Trình duyệt không hỗ trợ định vị GPS."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
      },
      (err) => {
        reject(err);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
      }
    );
  });
}


// =========================
// APPLY SORT – TOÀN BỘ GỌI BE
// =========================

async function applySort(sortValue) {
  currentSort = sortValue || null;

  if (!lastSearchParams.city || !lastSearchParams.target_date) {
    showToast("Hãy tìm lễ hội trước rồi mới dùng bộ lọc.");
    return;
  }

  enterListMode();

  // Không chọn sort -> lấy lại list mặc định từ BE
  if (!sortValue) {
    try {
      const data = await listEvents({
        city: lastSearchParams.city,
        target_date: lastSearchParams.target_date,
        session: lastSearchParams.session,
      });
      searchResults = data || [];
      renderSearchResults(searchResults);
    } catch (err) {
      console.error(err);
      showToast("Không thể tải danh sách.");
    }
    return;
  }

  // 1) GIÁ / ĐỘ NỔI TIẾNG -> gọi lại listEvents với sort param
  if (
    sortValue === "price_asc" ||
    sortValue === "price_desc" ||
    sortValue === "popularity_desc"
  ) {
    try {
      const data = await listEvents({
        city: lastSearchParams.city,
        target_date: lastSearchParams.target_date,
        session: lastSearchParams.session,
        sort: sortValue,
      });
      searchResults = data || [];
      renderSearchResults(searchResults);
    } catch (err) {
      console.error(err);
      showToast("Không thể sắp xếp theo bộ lọc đã chọn.");
    }
    return;
  }

  // 2) KHOẢNG CÁCH -> gọi /events/recommendations
  if (sortValue === "distance_asc") {
    try {
      const { lat, lng } = await getUserLocation();

      const onlyWithin5 =
        document.getElementById("filter-distance-5km")?.checked || false;

      const params = {
        city: lastSearchParams.city,
        target_date: lastSearchParams.target_date,
        session: lastSearchParams.session,
        lat,
        lng,
      };
      if (onlyWithin5) {
        params.max_distance_km = 5;
      }

      const recs = await getEventRecommendations(params);
      searchResults = recs || [];
      renderSearchResults(searchResults);
    } catch (err) {
      console.error("Không thể lọc theo khoảng cách:", err);
      showToast(
        "Không lấy được vị trí hiện tại, nên không lọc theo khoảng cách được."
      );
      renderSearchResults(searchResults);
    }
    return;
  }

  // sortValue lạ -> giữ nguyên list hiện tại
  renderSearchResults(searchResults);
}


// =========================
// RENDER LIST LỄ HỘI
// =========================

function renderSearchResults(list) {
  if (!eventListContainer) return;

  enterListMode();

  const headerHTML = `
    <div class="event-list-header">
      <div class="event-list-title">Kết quả tìm kiếm</div>
      <button id="event-list-back-btn" class="event-list-back-btn">
        Quay lại sách
      </button>
    </div>
  `;

  if (!list.length) {
    eventListContainer.innerHTML = `
      ${headerHTML}
      <div class="event-row no-events-row">
        <div class="event-row-title">
          Không có lễ hội/ sự kiện nào
        </div>
      </div>
    `;
  } else {
    const rowsHTML = list
      .map((e) => {
        const ten = e.name || "Không rõ";
        const thanhPho = e.city || "Không rõ";
        const giaVe = e.price_vnd || "Không rõ";
        const thoiGian = formatDateRange(e.start_datetime, e.end_datetime);
        const diaDiem = e.region || e.city || "Không rõ";
        const khoangCach =
          e.distance_km != null
            ? `${Number(e.distance_km).toFixed(1)} km`
            : "Không rõ";
        const imgUrl = e.image_url || e.img || "../images/default-event.jpg";

        return `
          <div class="event-row" data-event-id="${e.id}">
            <div class="event-row-inner">
              <div class="event-thumb" style="background-image: url('${imgUrl}')"></div>

              <div class="event-info">
                <div class="event-row-title">${ten}</div>

                <div class="event-row-field">
                  <span class="event-label">Thành phố:</span>
                  <span class="event-value">${thanhPho}</span>
                </div>

                <div class="event-row-field">
                  <span class="event-label">Giá vé:</span>
                  <span class="event-value">${giaVe}</span>
                </div>

                <div class="event-row-field">
                  <span class="event-label">Thời gian:</span>
                  <span class="event-value">${thoiGian}</span>
                </div>

                <div class="event-row-field">
                  <span class="event-label">Địa điểm tổ chức:</span>
                  <span class="event-value">${diaDiem}</span>
                </div>

                <div class="event-row-field">
                  <span class="event-label">Khoảng cách:</span>
                  <span class="event-value">${khoangCach}</span>
                </div>
              </div>
            </div>
          </div>
        `;
      })
      .join("");

    eventListContainer.innerHTML = headerHTML + rowsHTML;
  }

  const backBtn = document.getElementById("event-list-back-btn");
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      eventListContainer.innerHTML = "";
      enterBookMode();
    });
  }

  eventListContainer
    .querySelectorAll(".event-row")
    .forEach((row) => {
      const id = row.getAttribute("data-event-id");
      if (!id) return;
      row.addEventListener("click", () => openEventDetail(Number(id)));
    });
}
