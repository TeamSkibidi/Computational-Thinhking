/* --- Sidebar & Marker Logic --- */
const marker = document.querySelector('.nav-marker');
const blob = document.querySelector('.nav-blob');
const items = document.querySelectorAll('.nav-link');

function indicator(e) {
    marker.style.top = e.offsetTop + "px";
    marker.style.height = e.offsetHeight + "px";
    blob.style.top = e.offsetTop + "px";
    blob.style.height = e.offsetHeight + "px";
}

/* --- MAGIC SLIDER LOGIC --- */
const nextBtn = document.getElementById('next');
const prevBtn = document.getElementById('prev');
const carousel = document.querySelector('.carousel');
const listHTML = document.querySelector('.carousel .list');
const thumbnailHTML = document.querySelector('.carousel .thumbnail');

// Auto run logic
let timeRunning = 3000;
let timeAutoNext = 7000;
let runTimeOut;
let runNextAuto;

nextBtn.onclick = function(){
    showSlider('next');    
}

prevBtn.onclick = function(){
    showSlider('prev');    
}

function showSlider(type){
    const sliderItems = listHTML.querySelectorAll('.carousel .list .item');
    const thumbnailItems = thumbnailHTML.querySelectorAll('.carousel .thumbnail .item');
    
    if(type === 'next'){
        // Move first item to the end
        listHTML.appendChild(sliderItems[0]);
        thumbnailHTML.appendChild(thumbnailItems[0]);
        carousel.classList.add('next');
    }else{
        // Move last item to the start
        listHTML.prepend(sliderItems[sliderItems.length - 1]);
        thumbnailHTML.prepend(thumbnailItems[thumbnailItems.length - 1]);
        carousel.classList.add('prev');
    }

    // Clean up animation classes after they finish
    clearTimeout(runTimeOut);
    runTimeOut = setTimeout(() => {
        carousel.classList.remove('next');
        carousel.classList.remove('prev');
    }, 2000); // Matches animation duration somewhat

    // Reset auto play
    clearTimeout(runNextAuto);
    runNextAuto = setTimeout(() => {
        nextBtn.click();
    }, timeAutoNext);
}

// Start Auto Play
runNextAuto = setTimeout(() => {
    nextBtn.click();
}, timeAutoNext);


/* --- General UI Logic --- */
window.onload = () => {
    const activeLink = document.querySelector('.nav-link.active');
    if(activeLink) indicator(activeLink);
    checkAuth();
}

function switchTab(element, tabId) {
    items.forEach(item => item.classList.remove('active'));
    element.classList.add('active');
    indicator(element);

    const sections = document.querySelectorAll('section');
    sections.forEach(sec => sec.classList.remove('active-section'));
    const target = document.getElementById(tabId);
    if(target) target.classList.add('active-section');
}

document.getElementById('link-trip').addEventListener('click', function(e) {
    e.preventDefault();
    // Giữ hiệu ứng sidebar nếu muốn
    items.forEach(item => item.classList.remove('active'));
    this.classList.add('active');
    indicator(this);

// Chuyển sang trang gợi ý lịch trình
window.location.href = 'recommend.html'; // nếu Home.html và recommend.html cùng thư mục
});

document.getElementById('link-home').addEventListener('click', function(e) {
    e.preventDefault();
    // Giữ hiệu ứng sidebar nếu muốn
    items.forEach(item => item.classList.remove('active'));
    this.classList.add('active');
    indicator(this);

// Chuyển sang trang gợi ý lịch trình
window.location.href = 'home.html'; // nếu Home.html và recommend.html cùng thư mục
});


document.getElementById('link-search-visit').addEventListener('click', function(e) {
    e.preventDefault();
    // Giữ hiệu ứng sidebar nếu muốn
    items.forEach(item => item.classList    .remove('active'));
    this.classList.add('active');
    indicator(this);

// Chuyển sang trang gợi ý lịch trình
window.location.href = 'recommend_five_visitor.html'; // nếu Home.html và recommend.html cùng thư mục
});



/* --- Auth Logic --- */
function checkAuth() {
    const username = localStorage.getItem('travel_username');
    const authDisplay = document.getElementById('auth-display');
    if (username) {
        authDisplay.innerHTML = `
            <div class="user-profile">
                <!-- Nút đăng xuất hình tròn trước tên -->
                <button onclick="logout()" title="Đăng xuất" style="
                    width: 35px; 
                    height: 35px; 
                    border-radius: 50%; 
                    background: #ffe4e6; 
                    border: none; 
                    color: #f43f5e; 
                    cursor: pointer; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    transition: all 0.2s;
                    box-shadow: 0 4px 10px rgba(244, 63, 94, 0.2);
                " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                    <i class="fa-solid fa-power-off"></i>
                </button>

                <div class="user-info">
                    <h4 style="margin: 0; font-size: 0.95rem;">${username}</h4>
                    <span style="font-size: 0.75rem; color: #94a3b8;">Thành viên</span>
                </div>
            </div>`;
    } else {
        authDisplay.innerHTML = `
            <div class="auth-buttons">
                <button class="btn-auth btn-login" onclick="login()">Đăng nhập</button>
                <button class="btn-auth btn-register" onclick="login()">Đăng ký</button>
            </div>`;
    }
}
function login() {
    const name = prompt("Nhập tên hiển thị:", "Minh Travel");
    if(name) { localStorage.setItem('travel_username', name); checkAuth(); }
}
function logout() {
    if(confirm("Đăng xuất?")) { localStorage.removeItem('travel_username'); checkAuth(); }
}

/* --- Chatbot --- */
function sendMessage() {
    const input = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    if(input.value.trim()){
        chatBox.innerHTML += `<div class="message user-msg">${input.value}</div>`;
        input.value = '';
        setTimeout(() => chatBox.innerHTML += `<div class="message bot-msg">Tôi đang tìm kiếm thông tin...</div>`, 1000);
    }
}
document.getElementById('chat-input').addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMessage(); });