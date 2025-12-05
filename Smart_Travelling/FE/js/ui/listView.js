// js/ui/listView.js
// Render list kết quả tìm kiếm

import { formatDateRange } from "./detailView.js";

let eventListContainer = null;

// Khởi tạo, lấy reference container
export function initListView() {
  eventListContainer = document.getElementById("event-list-container");
}

// Render list
// options: { onRowClick(id), onBackToBook() }
export function renderSearchResults(list, options = {}) {
  if (!eventListContainer) return;

  const { onRowClick, onBackToBook } = options;

  const headerHTML = `
    <div class="event-list-header">
      <div class="event-list-title">Kết quả tìm kiếm</div>
      <button id="event-list-back-btn" class="event-list-back-btn">
        Quay lại sách
      </button>
    </div>
  `;

  if (!list || !list.length) {
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
        const giaVe = e.price_vnd ?? "Không rõ";
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

  // Nút back về sách
  const backBtn = document.getElementById("event-list-back-btn");
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      if (typeof onBackToBook === "function") {
        onBackToBook();
      }
    });
  }

  // Click từng dòng -> mở chi tiết
  eventListContainer.querySelectorAll(".event-row").forEach((row) => {
    const id = row.getAttribute("data-event-id");
    if (!id) return;
    row.addEventListener("click", () => {
      if (typeof onRowClick === "function") {
        onRowClick(Number(id));
      }
    });
  });
}
