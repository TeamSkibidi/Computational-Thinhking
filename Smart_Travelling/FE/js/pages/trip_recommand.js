import { 
    currentConfig, 
    updateConfig, 
    BLOCK_CONFIG, 
    AVAILABLE_TAGS 
} from "../services/trip.service.js";
import { 
    renderHeaderInfo, 
    renderDayNavigator, 
    renderDayTimeline 
} from "../ui/trip.render.js";

import { tripRecommand } from "../api/recommandApi.js";
document.addEventListener('DOMContentLoaded', () => init());

// === STATE ===
let generatedTripData = [];
let activeDayIndex = 0;

// === MAIN LOGIC ===
async function init() {
    // 1. GẮN SỰ KIỆN CHO CÁC NÚT (Event Listeners)
    
    // Nút: Tạo Lịch Trình
    const btnCreateTrip = document.getElementById('btnCreateTrip');
    if (btnCreateTrip) {
        btnCreateTrip.addEventListener('click', saveAndGenerate);
    }

    // Nút: Hủy bỏ 
    const btnCancelConfig = document.getElementById('btnCancelConfig');
    if (btnCancelConfig) {
        // Khi click thì gọi hàm toggleModal(false)
        btnCancelConfig.addEventListener('click', () => toggleModal(false));
    }
    
    // Nút đóng 
    const btnCloseX = document.querySelector('.modal-close-btn');
    if (btnCloseX) {
        btnCloseX.addEventListener('click', () => toggleModal(false));
    }


    // Logic Sidebar
    setupSidebarEvents();
    
    document.addEventListener("keydown", (e) => {
        const modal = document.getElementById('configModal');
        if (modal && modal.style.display === 'flex') return; // Nếu modal đang mở thì bỏ qua
        if (e.key === "ArrowLeft") handleDayChange(activeDayIndex - 1);
        if (e.key === "ArrowRight") handleDayChange(activeDayIndex + 1);
    });
    

    // Lấy dữ liệu chuyến đi từ LocalStorage (nếu có từ trước)
    generatedTripData = await getTrip();

    // Nếu có dữ liệu, hiển thị lên màn hình
    if (generatedTripData && generatedTripData.length > 0) {
        renderHeaderInfo(currentConfig);
        
        activeDayIndex = 0;
        renderDayNavigator(generatedTripData, 0, handleDayChange);
        renderDayTimeline(generatedTripData[0], 'none');
    }
}

// Hàm lấy dữ liệu từ LocalStorage
async function getTrip() {
    const tripStr = localStorage.getItem('trip');
    if (!tripStr) return [];
    
    const parsed = JSON.parse(tripStr);
    
    // Nếu là object có .days thì lấy .days, nếu là array thì dùng luôn
    if (Array.isArray(parsed)) {
        return parsed;
    } else if (parsed && parsed.days) {
        return Array.isArray(parsed.days) ? parsed.days : Object.values(parsed.days);
    }
    return [];
}

// Hàm này sẽ chạy khi sự kiện click xảy ra
async function saveAndGenerate() {
    // Thu thập dữ liệu từ các ô input
    const cityInput = document.getElementById('inputCity');
    const startDateInput = document.getElementById('inputStartDate');
    const numDaysInput = document.getElementById('inputNumDays');

    // Kiểm tra xem người dùng nhập đủ chưa
    if (!cityInput.value || !startDateInput.value || !numDaysInput.value) {
        alert("Vui lòng nhập đầy đủ Thành phố, Ngày bắt đầu và Số ngày!");
        return;
    }

    // Tạo object cấu hình để gửi lên Server
    const newConfig = {
        city: cityInput.value.trim(),
        start_date: startDateInput.value.trim(),
        num_days: parseInt(numDaysInput.value.trim()),
        
        preferred_tags: [],
        avoid_tags: [],
        max_leg_distance_km: 5.0,
        max_places_per_block: 3,
        must_visit_place_ids: [],
        avoid_place_ids: [],

        morning: {},
        lunch: {},
        afternoon: {},
        dinner: {},
        evening: {}
    };
    
    // Lấy các Tags (Sở thích) đã chọn (có class .active)
    document.querySelectorAll('.tag-btn.active').forEach(btn => {
        newConfig.preferred_tags.push(btn.dataset.tag);
    });

    // Lấy cấu hình thời gian cho từng khung
    BLOCK_CONFIG.forEach(block => {
        const enabled = document.getElementById(`toggle_${block.id}`).checked;
        const start = document.getElementById(`start_${block.id}`).value;
        const end = document.getElementById(`end_${block.id}`).value;
        newConfig[block.id] = { enabled, start, end };
    });

    // Gọi API
    try {
        const btnSubmit = document.getElementById('btnCreateTrip');
        const originalContent = btnSubmit.innerHTML;
        
        // Hiệu ứng Loading: Đổi nút thành "Đang tạo..." và xoay vòng
        btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang tạo...';
        btnSubmit.disabled = true;

        // Gọi hàm API
        const result = await tripRecommand(newConfig);
        console.log("Full result:", result);
        console.log("result.data:", result.data);
        console.log("result.data.days:", result.data?.days);

        // Khi thành công: Lấy dữ liệu trả về
        const trip = result.data;
        console.log("Thông tin Trip:", trip);
        const dayList = Array.isArray(trip.days) ? trip.days : Object.values(trip.days || {});

        // Lưu vào bộ nhớ trình duyệt
        localStorage.setItem("trip", JSON.stringify(dayList));
        generatedTripData = dayList;

        updateConfig(newConfig);
        
        // Đóng Modal cấu hình
        toggleModal(false);
            

        // Vẽ lại giao diện với dữ liệu mới
        renderHeaderInfo(newConfig);
        activeDayIndex = 0;
        renderDayNavigator(generatedTripData, 0, handleDayChange);
        renderDayTimeline(generatedTripData[0], 'fade');
        
        // Trả lại trạng thái nút ban đầu
        btnSubmit.innerHTML = originalContent;
        btnSubmit.disabled = false;

    } catch (err) {
        console.error(err);
        alert("Lỗi tạo lịch trình: " + (err.message || "Lỗi không xác định"));
        
        // Reset nút nếu lỗi
        const btnSubmit = document.getElementById('btnCreateTrip');
        if(btnSubmit) {
            btnSubmit.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Tạo Lịch Trình';
            btnSubmit.disabled = false;
        }
    }
}

// Modal Cấu Hình
function toggleModal(show) {
    const modal = document.getElementById('configModal');
    if(show) {
        initForm();
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('open'), 10);
        document.body.style.overflow = 'hidden';
    } else {
        modal.classList.remove('open');
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 300);
    }
}
// Hàm khởi tạo form với dữ liệu hiện tại
function initForm() {
    // ĐIỀN dữ liệu từ currentConfig VÀO các ô input (SỬA 3 DÒNG NÀY)
    document.getElementById('inputCity').value = currentConfig.city;
    document.getElementById('inputStartDate').value = currentConfig.start_date;
    document.getElementById('inputNumDays').value = currentConfig.num_days;

    // Render Tags (Giữ nguyên)
    const tagContainer = document.getElementById('tagSelectionArea');
    tagContainer.innerHTML = '';
    AVAILABLE_TAGS.forEach(tag => {
        const isActive = currentConfig.preferred_tags.includes(tag);
        const btn = document.createElement('button');
        btn.className = `tag-btn ${isActive ? 'active' : ''}`;
        btn.textContent = "#" + tag;
        btn.onclick = () => btn.classList.toggle('active');
        btn.dataset.tag = tag;
        tagContainer.appendChild(btn);
    });

    // Render Time Config (Giữ nguyên)
    const timeContainer = document.getElementById('timeConfigContainer');
    timeContainer.innerHTML = '';
    
    BLOCK_CONFIG.forEach(block => {
        const config = currentConfig[block.id] || { enabled: true, start: block.defaultStart, end: block.defaultEnd };
        
        const div = document.createElement('div');
        div.className = "time-config-item";
        
        div.innerHTML = `
            <div class="config-icon ${block.iconClass}"><i class="fa-solid ${block.icon}"></i></div>
            
            <div class="config-info">
                <div class="config-label">${block.label}</div>
                <div class="time-inputs">
                    <input type="time" id="start_${block.id}" class="time-control" value="${config.start}">
                    <span class="time-sep">-</span>
                    <input type="time" id="end_${block.id}" class="time-control" value="${config.end}">
                </div>
            </div>

            <div class="toggle-switch">
                <input type="checkbox" id="toggle_${block.id}" class="toggle-input" ${config.enabled ? 'checked' : ''}/>
                <label for="toggle_${block.id}" class="toggle-slider"></label>
            </div>
        `;
        timeContainer.appendChild(div);
    });
}

// Hàm gắn sự kiện cho sidebar
function setupSidebarEvents() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                this.classList.add('active');
                
                const blob = document.getElementById('navBlob');
                const relativeTop = this.offsetTop; 
                blob.style.top = `${relativeTop}px`;

                // 2. Logic based on ID
                if(this.id === 'navItemConfig') {
                    toggleModal(true);
                } else if(this.id === 'navItemTheme') {
                    toggleDarkMode();
                } else if(this.id === 'navItemSchedule') {
                    // Scroll to top
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
}

// Hàm Toggle Dark Mode (Tùy chọn)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
    
    const icon = document.querySelector('#navItemTheme i');
    if (icon) {
        icon.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
}

// Kiểm tra Dark Mode khi load trang
if (localStorage.getItem('darkMode') === 'enabled') {
    document.body.classList.add('dark-mode');
}



// Hàm xử lý khi chuyển ngày
function handleDayChange(newIndex) {
    if (newIndex < 0 || newIndex >= generatedTripData.length) return;
    
    const direction = newIndex > activeDayIndex ? 'right' : 'left';
    activeDayIndex = newIndex;
    
    renderDayTimeline(generatedTripData[newIndex], direction);
    renderDayNavigator(generatedTripData, activeDayIndex, handleDayChange);
}

// Nút mũi tên trái/phải
window.changeDay = (offset) => handleDayChange(activeDayIndex + offset);

// Expose functions to Window for HTML onclick
window.toggleModal = toggleModal;

// START APP
init();