import { 
  getTripHistory, 
  getTripDetail,
  deleteTrip, 
  deleteAllTrips 
} from "../api/tripHistoryApi.js";

// ===== STATE =====
let currentUser = null;

// ===== DOM ELEMENTS =====
const historyByDate = document.getElementById("historyByDate");
const emptyMessage = document.getElementById("emptyMessage");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const backToHomeBtn = document.getElementById("backToHomeBtn");
const tripDetailModal = document.getElementById("tripDetailModal");
const modalCloseBtn = document.getElementById("modalCloseBtn");
const tripDetailContent = document.getElementById("tripDetailContent");

// ===== INIT =====

async function init() {
  // Luôn gắn event cho nút quay lại (không phụ thuộc đăng nhập)
  backToHomeBtn?.addEventListener("click", () => {
    window.location.href = "recommend.html";
  });

  checkLoginStatus();
  
  if (!currentUser) {
    showNotLoggedIn();
    return;
  }
  
  await loadHistoryList();
  setupEventListeners();
}

function checkLoginStatus() {
  const savedUser = localStorage.getItem("user");
  if (savedUser) {
    currentUser = JSON.parse(savedUser);
  }
}

function showNotLoggedIn() {
  emptyMessage.classList.remove("hidden");
  emptyMessage.innerHTML = `
    <p>🔐 Bạn cần đăng nhập để xem lịch sử</p>
    <button class="btn btn-primary" onclick="window.location.href='../html/login.html'">
      Đăng nhập ngay
    </button>
  `;
}

// ===== LOAD HISTORY =====

async function loadHistoryList() {
  try {
    const data = await getTripHistory(currentUser.id);
    const tripsByDate = data.trips_by_date || {};

    historyByDate.innerHTML = "";

    if (Object.keys(tripsByDate).length === 0) {
      emptyMessage.classList.remove("hidden");
      return;
    }

    emptyMessage.classList.add("hidden");

    Object.entries(tripsByDate).forEach(([date, trips]) => {
      const dateSection = createDateSection(date, trips);
      historyByDate.appendChild(dateSection);
    });
  } catch (err) {
    console.error("Lỗi load lịch sử:", err);
    emptyMessage.classList.remove("hidden");
    emptyMessage.textContent = "❌ Lỗi tải lịch sử. Vui lòng thử lại.";
  }
}

// ===== CREATE DATE SECTION =====

function createDateSection(date, trips) {
  const section = document.createElement("div");
  section.className = "date-section";

  const dateHeader = document.createElement("div");
  dateHeader.className = "date-header";
  dateHeader.innerHTML = `
    <h3>📅 ${formatDate(date)} (${trips.length} chuyến)</h3>
  `;
  section.appendChild(dateHeader);

  const tripsList = document.createElement("div");
  tripsList.className = "trips-list";

  trips.forEach((trip) => {
    const card = createTripCard(trip);
    tripsList.appendChild(card);
  });

  section.appendChild(tripsList);
  return section;
}

// ===== CREATE TRIP CARD =====

function createTripCard(trip) {
  const div = document.createElement("div");
  div.className = "trip-card";

  const costFormatted = (trip.total_cost || 0).toLocaleString("vi-VN");
  const timeCreated = new Date(trip.created_at).toLocaleTimeString("vi-VN");

  div.innerHTML = `
    <div class="trip-card-header">
      <h4 class="trip-title">${trip.city}</h4>
      <span class="trip-time">${timeCreated}</span>
    </div>

    <div class="trip-card-info">
      <p>📅 ${trip.num_days} ngày</p>
      <p>👥 ${trip.num_people} người</p>
      <p>💰 ${costFormatted} VND</p>
    </div>

    <div class="trip-card-actions">
      <button class="btn btn-outline btn-sm view-btn" data-trip-id="${trip.id}">
        👁️ Xem chi tiết
      </button>
      <button class="btn btn-ghost btn-sm delete-btn" data-trip-id="${trip.id}">
        🗑️ Xóa
      </button>
    </div>
  `;

  return div;
}

// ===== EVENTS =====

function setupEventListeners() {
  historyByDate.addEventListener("click", async (e) => {
    if (e.target.closest(".view-btn")) {
      const tripId = parseInt(e.target.closest(".view-btn").dataset.tripId);
      await showTripDetail(tripId);
    }

    if (e.target.closest(".delete-btn")) {
      const tripId = parseInt(e.target.closest(".delete-btn").dataset.tripId);
      await handleDeleteTrip(tripId);
    }
  });

  clearHistoryBtn?.addEventListener("click", handleDeleteAll);
  modalCloseBtn?.addEventListener("click", closeModal);
  tripDetailModal?.addEventListener("click", (e) => {
    if (e.target === tripDetailModal) closeModal();
  });
}

// ===== SHOW TRIP DETAIL =====

async function showTripDetail(tripId) {
  try {
    const trip = await getTripDetail(tripId, currentUser.id);

    // Lưu trip vào localStorage để trang recommend đọc lại
    localStorage.setItem("trip_from_history", JSON.stringify(trip));

    // Chuyển sang trang recommend
    window.location.href = "../html/recommend.html?fromHistory=1";
  } catch (err) {
    console.error("Lỗi:", err);
    alert("❌ Lỗi tải chi tiết trip");
  }
}

function closeModal() {
  tripDetailModal?.classList.add("hidden");
}

// ===== DELETE =====

async function handleDeleteTrip(tripId) {
  if (!confirm("Xóa lịch trình này?")) return;

  try {
    await deleteTrip(tripId, currentUser.id);
    await loadHistoryList();
    alert("✅ Xóa thành công");
  } catch (err) {
    console.error("Lỗi:", err);
    alert("❌ Lỗi xóa trip");
  }
}

async function handleDeleteAll() {
  if (!confirm("Xóa toàn bộ lịch sử?")) return;

  try {
    await deleteAllTrips(currentUser.id);
    await loadHistoryList();
    alert("✅ Xóa toàn bộ thành công");
  } catch (err) {
    console.error("Lỗi:", err);
    alert("❌ Lỗi xóa");
  }
}

// ===== HELPERS =====

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("vi-VN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric"
  });
}

// ===== RUN =====

document.addEventListener("DOMContentLoaded", init);