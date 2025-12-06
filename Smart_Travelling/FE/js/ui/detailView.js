// js/ui/detailView.js
// Overlay chi tiết + toast + helper format date

let eventDetailOverlay = null;
let eventDetailContent = null;
let toastEl = null;
let toastTimeoutId = null;

// ===== DATE HELPERS =====
function formatFullDate(isoString) {
  if (!isoString) return "Không rõ";
  const d = new Date(isoString);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}

export function formatDateRange(startIso, endIso) {
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

// ===== TOAST =====
export function showToast(message) {
  if (!toastEl) return;

  if (toastTimeoutId) {
    clearTimeout(toastTimeoutId);
    toastTimeoutId = null;
  }

  toastEl.textContent = message;
  toastEl.classList.remove("hidden");
  toastEl.classList.add("show");

  toastTimeoutId = setTimeout(() => {
    toastEl.classList.remove("show");
    toastEl.classList.add("hidden");
  }, 3000);
}

// ===== DETAIL HTML BUILDERS =====
function buildEventDetailHTML(e) {
  const imgUrl = e.image_url || "../images/Trung_Thu.jpg";
  const cityRegion = e.region ? `${e.city}, ${e.region}` : e.city || "Không rõ";
  const timeRange = formatDateRange(e.start_datetime, e.end_datetime);
  const price = e.price_vnd ?? "Không rõ";
  const popularity =
    e.popularity != null ? Number(e.popularity).toFixed(1) : "Không rõ";
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

function buildBookEventDetailHTML(ev) {
  const imgUrl = ev.img || "../images/default-event.jpg";
  const timeText = ev.date || "Thời gian: không rõ";
  const locText = ev.loc || "Toàn quốc";

  return `
    <div class="event-detail-body">
      <div class="event-detail-image" style="background-image:url('${imgUrl}')"></div>
      <div class="event-detail-info">
        <div class="event-detail-title">${ev.name}</div>
        <div class="event-detail-meta">${locText}</div>
        <div class="event-detail-meta">Thời gian: ${timeText}</div>

        <div class="event-detail-summary">
          ${ev.detail || ev.desc || ""}
        </div>

        <div class="event-detail-tags">
          ${
            (ev.tags || [])
              .map((t) => `<span class="event-detail-tag">${t}</span>`)
              .join("")
          }
        </div>
      </div>
    </div>
  `;
}

// ===== OVERLAY CONTROL =====
function openOverlay(htmlContent) {
  if (!eventDetailOverlay || !eventDetailContent) return;

  eventDetailOverlay.classList.remove("hidden");
  eventDetailOverlay.classList.add("show");
  eventDetailContent.innerHTML = htmlContent;

  if (window.lucide) lucide.createIcons();
}

export function closeEventDetail() {
  if (!eventDetailOverlay) return;
  eventDetailOverlay.classList.remove("show");
  eventDetailOverlay.classList.add("hidden");
}

// Public APIs cho controller dùng
export function showEventDetail(eventData) {
  openOverlay(buildEventDetailHTML(eventData));
}

export function showBookEventDetail(bookEventData) {
  openOverlay(buildBookEventDetailHTML(bookEventData));
}

// ===== INIT =====
export function initDetailView() {
  eventDetailOverlay = document.getElementById("event-detail-overlay");
  eventDetailContent = document.getElementById("event-detail-content");
  toastEl = document.getElementById("event-toast");

  const closeBtn = document.getElementById("event-detail-close");
  if (closeBtn) {
    // truyền reference của hàm, KHÔNG gọi luôn
    closeBtn.addEventListener("click", closeEventDetail);
  }


  if (eventDetailOverlay) {
    eventDetailOverlay.addEventListener("click", (e) => {
      if (e.target === eventDetailOverlay) {
        closeEventDetail();
      }
    });
  }
}
