const admin = document.getElementById("admin");

// Check if the element exists to avoid errors
if (admin) {
  // If the element is an anchor and already has href, rely on that (works without JS too).
  // But also add a click handler as an explicit fallback.
  admin.addEventListener('click', function(e) {
    // If the element is an <a> tag, default behavior will handle navigation.
    // For safety, prevent default and navigate programmatically to ensure consistent behavior.
    e.preventDefault();
    window.location.href = '../HTML/user.html';
  });
}
 
 
 
 
 
 
 
 
 
 const nextBtn = document.getElementById("nextBtn");
    const page2 = document.getElementById("page2");
    let currentPage = 1; // Trang hiện tại (1 hoặc 2)

    // === NÚT BẤM ===
    nextBtn.addEventListener("click", () => showPage(2));

    // === HÀM CHUYỂN TRANG ===
    function showPage(page) {
      if (page === 2) {
        page2.style.top = "0";
        currentPage = 2;
      } else {
        page2.style.top = "100%";
        currentPage = 1;
      }
    }

    // === LƯỚT CHUỘT ===
    window.addEventListener("wheel", (e) => {
      if (e.deltaY > 0 && currentPage === 1) showPage(2);
      else if (e.deltaY < 0 && currentPage === 2) showPage(1);
    });

    // === LƯỚT CẢM ỨNG (Mobile) ===
    let startY = 0;
    window.addEventListener("touchstart", (e) => startY = e.touches[0].clientY);
    window.addEventListener("touchend", (e) => {
      const diff = startY - e.changedTouches[0].clientY;
      if (diff > 50 && currentPage === 1) showPage(2);
      else if (diff < -50 && currentPage === 2) showPage(1);
    });








// Toggle sidebar
function toggleSidebar() {
  console.log('toggleSidebar called');
  document.getElementById("sidebar").classList.toggle("visible");
}

// Filter categories
function filterCategory(category) {
  const cards = document.querySelectorAll(".destination-card");
  cards.forEach((card) => {
    if (category === "all" || card.dataset.category === category) {
      card.style.display = "flex";
      card.classList.add("loaded");
      card.classList.remove("hidden");
    } else {
      card.style.display = "none";
    }
  });
}

// Tabs
document.querySelectorAll(".search-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document
      .querySelectorAll(".search-tab")
      .forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
  });
});
// Open inline search when clicking the 'Tìm kiếm địa điểm' tab
const openSearchBtn = document.getElementById('openSearch');
const sidebarSearch = document.getElementById('sidebarSearch');
const placeInput = document.getElementById('placeSearchInput');
const searchSubmit = document.getElementById('searchSubmit');
if (openSearchBtn && sidebarSearch) {
  openSearchBtn.addEventListener('click', (e) => {
    e.preventDefault();
    sidebarSearch.classList.toggle('active');
    if (sidebarSearch.classList.contains('active')) {
      placeInput.focus();
    }
  });
}

function submitSearchQuery() {
  const q = placeInput.value.trim();
  if (!q) return;
  // Redirect to testmap with query param (simple approach)
  window.location.href = `/testmap.html?q=${encodeURIComponent(q)}`;
}

if (searchSubmit) searchSubmit.addEventListener('click', submitSearchQuery);
if (placeInput) placeInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submitSearchQuery();
});

// Infinite scroll
let isLoading = false;
let loadCount = 0;
const maxLoads = 1;
const grid = document.getElementById("destinationsGrid");
const loading = document.getElementById("loadingSpinner");

function loadMoreCards() {
  if (isLoading || loadCount >= maxLoads) return;
  loadCount++;
  isLoading = true;
  loading.style.display = "block";

  const newCards = [
    {
         title: "",
    cat: "dong-bang",
    desc: "Phong Nha - Kẻ bàn là điểm đến kì thú và cực kì đặc biệt trên thế giới mà bạn nên đến một lần trong đời .",
    price: "200.000 VNĐ",
    rating: "10/10",
    backgroundPosition: "bottom",
    image: "../image/name5.png"
  },
  {
    title: "",
    cat: "dong-bang",
    desc: "Khám phá các bãi biển và bờ át trắng xoá bên cạnh thành phố náo nhiệt năng động .",
    price: "150.000 VNĐ",
    rating: "8.5/10",
    backgroundPosition: "center",
    image: "../image/name6.png"
  },
  ];

  setTimeout(() => {
    newCards.forEach((cardData) => {
      const card = document.createElement("div");
      card.className = "destination-card hidden";
      card.dataset.category = cardData.cat;
      card.innerHTML = `
        <div class="destination-image" 
            style=" background-image: url('${cardData.image}');
         background-position: ${cardData.backgroundPosition || 'center'};
         background-size: cover;
         background-repeat: no-repeat;
       ">
          <div class="destination-overlay"><h2 class="destination-title">${cardData.title}</h2></div>
        </div>
        <p class="destination-description">${cardData.desc}</p>
        <div class="destination-footer"><span>Giá từ: ${cardData.price}</span><span>⭐ ${cardData.rating}</span></div>
      `;
      grid.insertBefore(card, loading);
      setTimeout(() => {
        card.classList.add("loaded");
        card.classList.remove("hidden");
      }, 100);
    });
    loading.style.display = "none";
    isLoading = false;
  }, 1000);
}

window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
    loadMoreCards();
  }
});

// Lazy load
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("loaded");
      entry.target.classList.remove("hidden");
      observer.unobserve(entry.target);
    }
  });
});
document.querySelectorAll(".destination-card").forEach((el) => observer.observe(el));

// Pull-to-refresh
