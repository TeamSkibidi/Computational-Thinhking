// ===== STATE =====
let isLoggedIn = false;
let currentUser = null;

// ===== DOM ELEMENTS =====
const sidebar = document.getElementById('sidebar');
const menuToggle = document.getElementById('menuToggle');
const sidebarClose = document.getElementById('sidebarClose');
const btnLogin = document.getElementById('btnLogin');
const profileName = document.getElementById('profileName');

const navRecommendTrip = document.getElementById('navRecommendTrip');
const navRecommendPlaces = document.getElementById('navRecommendPlaces');
const navEvents = document.getElementById('navEvents');

const btnGetStarted = document.getElementById('btnGetStarted');
const featureRecommendTrip = document.getElementById('featureRecommendTrip');
const featureRecommendPlaces = document.getElementById('featureRecommendPlaces');
const featureEvents = document.getElementById('featureEvents');

// ===== INITIALIZATION =====

function init() {
  checkLoginStatus();
  setupEventListeners();
}

// ===== LOGIN CHECK =====

function checkLoginStatus() {
  const savedUser = localStorage.getItem('user');
  
  if (savedUser) {
    try {
      currentUser = JSON.parse(savedUser);
      isLoggedIn = true;
      updateUILoggedIn();
    } catch (err) {
      console.error('Lỗi parse user:', err);
      isLoggedIn = false;
    }
  } else {
    isLoggedIn = false;
  }
}

function updateUILoggedIn() {
  if (isLoggedIn && currentUser) {
    profileName.textContent = currentUser.username || 'Người dùng';
    btnLogin.textContent = 'Đăng xuất';
  } else {
    profileName.textContent = 'Khách';
    btnLogin.textContent = 'Đăng nhập';
  }
}

// ===== EVENT LISTENERS =====

function setupEventListeners() {
  // Sidebar toggle
  menuToggle?.addEventListener('click', toggleSidebar);
  sidebarClose?.addEventListener('click', closeSidebar);

  // Login/Logout
  btnLogin?.addEventListener('click', handleLoginLogout);

  // Navigation
  navRecommendTrip?.addEventListener('click', () => navigateTo('../html/recommend.html'));
  navRecommendPlaces?.addEventListener('click', () => navigateTo('../html/recommend_five_vistor.html'));
  navEvents?.addEventListener('click', () => navigateTo('../html/event.html'));

  // Features buttons
  btnGetStarted?.addEventListener('click', () => navigateTo('../html/recommend_five_vistor.html'));
  featureRecommendTrip?.addEventListener('click', () => navigateTo('../html/recommend.html'));
  featureRecommendPlaces?.addEventListener('click', () => navigateTo('../html/recommend_five_vistor.html'));
  featureEvents?.addEventListener('click', () => navigateTo('../html/event.html'));

  // Close sidebar when clicking outside (mobile)
  document.addEventListener('click', (e) => {
    if (window.innerWidth < 768) {
      const isSidebarClick = sidebar?.contains(e.target);
      const isMenuToggleClick = menuToggle?.contains(e.target);
      
      if (!isSidebarClick && !isMenuToggleClick && sidebar?.classList.contains('visible')) {
        closeSidebar();
      }
    }
  });
}

// ===== SIDEBAR FUNCTIONS =====

function toggleSidebar() {
  sidebar?.classList.toggle('visible');
}

function closeSidebar() {
  sidebar?.classList.remove('visible');
}

// ===== LOGIN/LOGOUT =====

function handleLoginLogout() {
  if (isLoggedIn) {
    // Logout
    if (confirm('Bạn có chắc chắn muốn đăng xuất?')) {
      localStorage.removeItem('user');
      isLoggedIn = false;
      currentUser = null;
      updateUILoggedIn();
      alert('Đã đăng xuất thành công');
    }
  } else {
    // Login
    window.location.href = '../html/login.html';
  }
}

// ===== NAVIGATION =====

function navigateTo(path) {
  window.location.href = path;
}

// ===== RUN ON DOM LOAD =====

document.addEventListener('DOMContentLoaded', init);