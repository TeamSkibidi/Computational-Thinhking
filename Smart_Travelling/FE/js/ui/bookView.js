// js/ui/bookView.js
// Quản lý "quyển sách" lễ hội: hiển thị & auto lật

let bookWrapper;
let staticLeft;
let staticRight;

let currentIndex = 0;
let isAnimating = false;
let flipIntervalId = null;
let isBookMode = true;

// callback do controller truyền vào, để mở chi tiết book event
let onBookDetailClickCb = null;

// DATA CỐ ĐỊNH CHO SÁCH
const bookEvents = [
  {
    id: 1,
    name: "Tết Nguyên Đán",
    date: "01 - 03 Tháng 1 (Âm Lịch)",
    loc: "Toàn Quốc",
    theme: "theme-tet",
    img: "../images/Tet.jpg",
    desc: "Chào đón năm mới...",
    tags: ["Truyền thống", "Gia đình"],
    particle: "🌸",
    detail: `
      <p>Tết Nguyên Đán là dịp lễ lớn nhất trong năm, đánh dấu thời khắc chuyển giao giữa năm cũ và năm mới.</p>
      <ul>
        <li>Phong tục: chúc Tết, lì xì, hái lộc, đi chùa đầu năm...</li>
        <li>Món ăn tiêu biểu: bánh chưng, bánh tét, dưa hành, thịt kho hột vịt...</li>
        <li>Không khí: sum họp gia đình, nghỉ lễ dài ngày trên khắp cả nước.</li>
      </ul>
    `,
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
    detail: `
      <p>Tết Trung Thu là ngày hội dành cho thiếu nhi với lồng đèn, múa lân và bánh trung thu.</p>
      <ul>
        <li>Hoạt động: rước đèn, phá cỗ, xem múa lân, xem múa rối.</li> 
        <li>Ý nghĩa: đoàn viên, chăm sóc và bày tỏ tình cảm với trẻ nhỏ.</li>
      </ul>
    `,
  },
   {
     id: 3,
     name: "Giỗ Tổ Hùng Vương",
     date: "10 Tháng 3 (Âm Lịch)",
     loc: "Toàn Quốc",
     theme: "theme-gioto",
     img: "../images/Hung_Vuong.jpg",
     desc: "Ngày tưởng nhớ các Vua Hùng.",
     tags: ["Lịch sử", "Tín ngưỡng"],
     particle: "🗻",
     detail: `
       <p>Giỗ Tổ Hùng Vương là ngày lễ để tưởng nhớ công ơn dựng nước của các Vua Hùng.</p>
       <ul>
         <li>Trọng tâm diễn ra tại Đền Hùng (Phú Thọ) với lễ rước, dâng hương, tế lễ trang nghiêm.</li>
         <li>Cả nước tổ chức dâng hương, hoạt động văn hóa, giáo dục lịch sử dân tộc cho thế hệ trẻ.</li>
         <li>Khẩu hiệu quen thuộc: "Dù ai đi ngược về xuôi, nhớ ngày Giỗ Tổ mùng 10 tháng 3".</li>
       </ul>
     `,
   },
   {
     id: 5,
     name: "Lễ Vu Lan Báo Hiếu",
     date: "15 Tháng 7 (Âm Lịch)",
     loc: "Toàn Quốc",
     theme: "theme-vulan",
     img: "../images/Vu_Lan.jpg",
     desc: "Mùa báo hiếu cha mẹ, ông bà.",
     tags: ["Gia đình", "Tâm linh"],
     particle: "💐",
     detail: `
       <p>Vu Lan là mùa báo hiếu, nhắc nhở con cháu ghi nhớ công ơn sinh thành dưỡng dục của cha mẹ, tổ tiên.</p>
       <ul>
         <li>Phong tục: cài hoa hồng, lễ chùa, cầu siêu, làm việc thiện, sum họp gia đình.</li>
         <li>Ý nghĩa: trân trọng những người thân yêu, lan tỏa tinh thần yêu thương và chia sẻ.</li>
         <li>Được xem như một trong những ngày lễ giàu tính nhân văn của người Việt.</li>
       </ul>
     `,
   },
   {
     id: 6,
     name: "Giải phóng Miền Nam & Quốc tế Lao động",
     date: "30 Tháng 4 - 01 Tháng 5 (Dương Lịch)",
     loc: "Toàn Quốc",
     theme: "theme-304-15",
     img: "../images/Giai_phong_mien_Nam.jpg",
     desc: "Kỷ niệm ngày thống nhất đất nước và tôn vinh người lao động.",
     tags: ["Lịch sử", "Nghỉ lễ"],
     particle: "🇻🇳",
     detail: `
       <p>Hai ngày lễ 30/4 và 1/5 thường được nghỉ liền kề, là dịp người dân cả nước tưởng nhớ lịch sử và nghỉ ngơi, du lịch.</p>
       <ul>
         <li>30/4: kỷ niệm ngày giải phóng miền Nam, thống nhất đất nước.</li>
         <li>01/5: ngày Quốc tế Lao động, tôn vinh người lao động trên toàn thế giới.</li>
         <li>Hoạt động: mít tinh, diễu hành, xem bắn pháo hoa, tham gia các chuyến du lịch nghỉ dưỡng.</li>
       </ul>
     `,
   },
   {
     id: 7,
     name: "Quốc khánh Việt Nam",
     date: "02 Tháng 9 (Dương Lịch)",
     loc: "Toàn Quốc",
     theme: "theme-quockhanh",
     img: "../images/Quoc_Khanh.jpg",
     desc: "Ngày khai sinh nước Việt Nam Dân chủ Cộng hòa.",
     tags: ["Lịch sử", "Tự hào dân tộc"],
     particle: "🎆",
     detail: `
       <p>Quốc khánh 2/9 là ngày lễ lớn đánh dấu sự ra đời của Nhà nước Việt Nam hiện đại.</p>
       <ul>
         <li>Hoạt động: lễ chào cờ, mít tinh, các chương trình nghệ thuật, bắn pháo hoa tại nhiều địa phương.</li>
         <li>Người dân thường kết hợp nghỉ ngơi, về quê thăm gia đình hoặc đi du lịch.</li>
         <li>Không khí: ngập tràn cờ đỏ sao vàng trên khắp đường phố, quảng trường, công sở.</li>
       </ul>
     `,
   },
   {
     id: 8,
     name: "Giáng Sinh (Noel)",
     date: "24 - 25 Tháng 12 (Dương Lịch)",
     loc: "Toàn Quốc",
     theme: "theme-noel",
     img: "../images/Noel.jpg",
     desc: "Không khí mùa đông lung linh đèn màu.",
     tags: ["Tôn giáo", "Giới trẻ"],
     particle: "🎄",
     detail: `
       <p>Giáng Sinh vốn là lễ tôn giáo của người theo đạo Thiên Chúa, nhưng hiện nay đã trở thành dịp vui chơi quen thuộc với giới trẻ Việt Nam.</p>
       <ul>
         <li>Hoạt động: trang trí cây thông, hang đá, đi lễ nhà thờ, tặng quà, chụp ảnh check-in.</li>
         <li>Các trung tâm thương mại, phố đi bộ, nhà thờ được trang hoàng rực rỡ, đông đúc.</li>
         <li>Không khí: ấm áp, lãng mạn với đèn trang trí, nhạc Giáng Sinh vang khắp nơi.</li>
       </ul>
     `,
   },
   {
     id: 9,
     name: "Ngày Quốc tế Phụ nữ",
     date: "08 Tháng 3 (Dương Lịch)",
     loc: "Toàn Quốc",
     theme: "theme-8-3",
     img: "../images/Quoc_te_phu_nu.jpg",
     desc: "Tôn vinh phụ nữ Việt Nam và thế giới.",
     tags: ["Gia đình", "Xã hội"],
     particle: "🌹",
     detail: `
       <p>Ngày Quốc tế Phụ nữ 8/3 là dịp mọi người bày tỏ tình cảm, lòng biết ơn đối với bà, mẹ, vợ, cô giáo và những người phụ nữ xung quanh.</p>
       <ul>
         <li>Hoạt động: tặng hoa, quà, tổ chức văn nghệ, gặp mặt, tri ân phụ nữ tại cơ quan và gia đình.</li>
         <li>Ý nghĩa: khẳng định vai trò, đóng góp quan trọng của phụ nữ trong xã hội hiện đại.</li>
         <li>Không khí: rộn ràng ở trường học, công ty, đường phố với nhiều chương trình giảm giá, quà tặng dành cho chị em.</li>
       </ul>
     `,
   },
];


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
        <button
          type="button"
          class="book-detail-btn px-6 py-3 bg-[var(--theme-primary)] text-white rounded shadow-lg hover:shadow-xl transition transform hover:-translate-y-1 flex items-center gap-2"
        >
          Xem chi tiết <i data-lucide="arrow-right" width="16"></i>
        </button>
      </div>
    </div>
  `;
}

function updateBodyTheme(themeClass) {
  document.body.className = themeClass;
}

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

function renderStaticPage(leftIndex, rightIndex) {
  staticLeft.innerHTML = getImageHTML(bookEvents[leftIndex]);
  staticRight.innerHTML = getTextHTML(bookEvents[rightIndex]);

  staticLeft.className = `static-page static-left ${bookEvents[leftIndex].theme}`;
  staticRight.className = `static-page static-right ${bookEvents[rightIndex].theme}`;

  attachBookDetailButton();
}

function attachBookDetailButton() {
  if (!staticRight) return;
  const btn = staticRight.querySelector(".book-detail-btn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    if (typeof onBookDetailClickCb === "function") {
      onBookDetailClickCb(bookEvents[currentIndex]);
    }
  });
}

function flipToNext() {
  if (!isBookMode) return;

  if (isAnimating || bookEvents.length === 0) return;
  isAnimating = true;

  const nextIndex = (currentIndex + 1) % bookEvents.length;
  const currentData = bookEvents[currentIndex];
  const nextData = bookEvents[nextIndex];

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

  if (window.lucide) lucide.createIcons();

  setTimeout(() => startParticles(nextData.particle), 500);

  setTimeout(() => {
    staticLeft.innerHTML = getImageHTML(nextData);
    staticLeft.className = `static-page static-left ${nextData.theme}`;
    flipper.remove();
    currentIndex = nextIndex;
    isAnimating = false;
    if (window.lucide) lucide.createIcons();
    attachBookDetailButton();
  }, 2000);
}

// === API PUBLIC ===

// Khởi tạo book view
export function initBookView({ onBookDetailClick } = {}) {
  bookWrapper = document.getElementById("bookWrapper");
  staticLeft = document.getElementById("staticLeft");
  staticRight = document.getElementById("staticRight");

  onBookDetailClickCb = onBookDetailClick || null;

  if (!bookWrapper || !staticLeft || !staticRight || !bookEvents.length) return;

  currentIndex = 0;
  renderStaticPage(currentIndex, currentIndex);

  updateBodyTheme(bookEvents[currentIndex].theme);
  if (window.lucide) lucide.createIcons();
  startParticles(bookEvents[currentIndex].particle);

  if (flipIntervalId) clearInterval(flipIntervalId);
  flipIntervalId = setInterval(flipToNext, 5000);
}

// Bật chế độ SÁCH: hiện sách, ẩn UI list (ở CSS dùng class show-list)
export function enterBookMode() {
  if (bookWrapper) {
    isBookMode = true;
    bookWrapper.classList.remove("show-list");

     // bật lại auto flip nếu đang tắt
    if (!flipIntervalId) {
      flipIntervalId = setInterval(flipToNext, 5000);
    }
  }

}

// Bật chế độ LIST: ẩn sách (bookWrapper sẽ chuyển state qua CSS)
export function enterListMode() {
  if (bookWrapper) {
    isBookMode = false;
    bookWrapper.classList.add("show-list");

    // tắt auto flip
    if (flipIntervalId) {
      clearInterval(flipIntervalId);
      flipIntervalId = null;
    }
  }
}
