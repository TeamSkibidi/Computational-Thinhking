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
import { getTags } from "../api/tagsApi.js";

// === STATE ===
let generatedTripData = [];
let activeDayIndex = 0;
let cachedTags = [];
let currentUser = null;


// === INIT ===
document.addEventListener('DOMContentLoaded', () => init());

function loadTripFromHistoryIfAny() {
    const raw = localStorage.getItem("trip_from_history");
    if (!raw) return false;

    try {
        const trip = JSON.parse(raw);
        console.log("🔁 Load trip from history:", trip);



        // Cập nhật cấu hình hiện tại từ trip
        currentConfig.city = trip.city || currentConfig.city;
        currentConfig.start_date = trip.start_date || currentConfig.start_date;
        currentConfig.num_days = trip.num_days || currentConfig.num_days;
        currentConfig.num_people = trip.num_people || currentConfig.num_people || 1;
        currentConfig.preferred_tags = trip.tags || trip.preferred_tags || [];

        // Parse lại days giống như lúc gọi API
        let days = [];
        const tripData = trip.trip_data || trip.data || trip;

        if (Array.isArray(tripData?.days)) {
            days = tripData.days;
        } else if (tripData?.days && typeof tripData.days === "object") {
            days = Object.values(tripData.days);
        } else if (Array.isArray(tripData)) {
            days = tripData;
        }

        console.log("Days from history:", days);

        generatedTripData = days;
        activeDayIndex = 0;

        // Render lại giống lúc vừa tạo trip
        renderHeaderInfo(currentConfig, generatedTripData);
        renderDayNavigator(generatedTripData, activeDayIndex, switchToDay);

        if (generatedTripData.length > 0) {
            renderDayTimeline(generatedTripData[0], "fade");
        }

        return true;
    } catch (e) {
        console.error("Lỗi parse trip_from_history:", e);
        return false;
    } finally {
        // Dùng xong thì xóa, tránh reload lại vẫn còn
        localStorage.removeItem("trip_from_history");
    }
}

async function init() {
    console.log("Initializing...");

    checkLoginStatus();
    
    // Fetch tags ngay khi load trang
    await fetchAndCacheTags();
    
    // Setup events
    setupModalEvents();
    setupTagsDropdown();
    
    // Chỉ load từ history nếu URL có ?fromHistory=1
    const params = new URLSearchParams(window.location.search);
    const fromHistory = params.get("fromHistory") === "1";

    if (fromHistory) {
        const loaded = loadTripFromHistoryIfAny();
        if (!loaded) {
            // Nếu vì lý do gì đó không load được thì quay về trạng thái mặc định
            renderHeaderInfo(currentConfig);
        }
    } else {
        // Mở trang bình thường -> không đụng gì tới history
        renderHeaderInfo(currentConfig);
    }
    
    console.log("Init complete!");
}


// ✅ THÊM: Check login status
function checkLoginStatus() {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            console.log("Current user:", currentUser);
        } catch (e) {
            console.error("Parse user error:", e);
        }
    }
}
// === FETCH TAGS ===
async function fetchAndCacheTags() {
    try {
        console.log("Fetching tags from API...");
        const result = await getTags();
        console.log("API Response:", result);
        
        // Xử lý các kiểu response khác nhau
        if (result && result.data && Array.isArray(result.data)) {
            cachedTags = result.data;
        } else if (Array.isArray(result)) {
            cachedTags = result;
        } else {
            console.warn("Invalid response, using defaults");
            cachedTags = [...AVAILABLE_TAGS];
        }
        
        console.log("Cached tags:", cachedTags);
        localStorage.setItem("tags", JSON.stringify(cachedTags));
        
    } catch (error) {
        console.error("Fetch tags failed:", error);
        
        // Fallback
        const stored = localStorage.getItem("tags");
        cachedTags = stored ? JSON.parse(stored) : [...AVAILABLE_TAGS];
        console.log("Using fallback tags:", cachedTags);
    }
}

// === SETUP MODAL EVENTS ===
function setupModalEvents() {
    // Floating button
    document.querySelector('.btn-floating-config')?.addEventListener('click', () => toggleModal(true));
    
    // Sidebar "Cấu hình"
    document.getElementById('navItemConfig')?.addEventListener('click', () => toggleModal(true));
    
    // Sidebar "Lịch trình"  
    document.getElementById('navItemSchedule')?.addEventListener('click', () => toggleModal(false));
    
    // ⭐ Sidebar "Đã lưu" -> mở history
    const savedItem = document.getElementById('navItemSaved');
    if (savedItem) {
        savedItem.addEventListener('click', () => {
            console.log("👉 Click ĐÃ LƯU – chuyển sang history");
            window.location.href = "./history.html";  // hoặc "history.html"
        });
    } else {
        console.warn("Không tìm thấy #navItemSaved trong DOM");
    }

    // Close buttons
    document.querySelector('.modal-close-btn')?.addEventListener('click', () => toggleModal(false));
    document.getElementById('btnCancelConfig')?.addEventListener('click', () => toggleModal(false));
    
    // Create trip button
    document.getElementById('btnCreateTrip')?.addEventListener('click', handleCreateTrip);
    
    // Click overlay to close
    document.getElementById('configModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'configModal') toggleModal(false);
    });
}

// === SETUP TAGS DROPDOWN ===
function setupTagsDropdown() {
    const trigger = document.getElementById('tagsTrigger');
    const dropdown = document.getElementById('tagsDropdown');
    
    if (!trigger || !dropdown) {
        console.warn("Tags dropdown elements not found");
        return;
    }
    
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = dropdown.classList.contains('open');
        
        trigger.classList.toggle('active', !isOpen);
        dropdown.classList.toggle('open', !isOpen);
    });
    
    document.addEventListener('click', (e) => {
        if (!trigger.contains(e.target) && !dropdown.contains(e.target)) {
            trigger.classList.remove('active');
            dropdown.classList.remove('open');
        }
    });
}

// === TOGGLE MODAL ===
async function toggleModal(show) {
    const modal = document.getElementById('configModal');
    if (!modal) return;
    
    if (show) {
        console.log("Opening modal...");
        
        // Fetch tags nếu chưa có
        if (cachedTags.length === 0) {
            await fetchAndCacheTags();
        }
        
        // Render form với tags
        renderModalForm();
        
        // Show modal
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

// === RENDER MODAL FORM ===
function renderModalForm() {
    console.log("Rendering form...");
    
    // Basic inputs
    const inputCity = document.getElementById('inputCity');
    const inputStartDate = document.getElementById('inputStartDate');
    const inputNumDays = document.getElementById('inputNumDays');
    const inputNumPeople = document.getElementById('inputNumPeople');
    
    if (inputCity) inputCity.value = currentConfig.city || 'Hà Nội';
    if (inputStartDate) inputStartDate.value = currentConfig.start_date || getTodayDate();
    if (inputNumDays) inputNumDays.value = currentConfig.num_days || 3;
    if (inputNumPeople) inputNumPeople.value = currentConfig.num_people || 1;
    
    // Render tags
    renderTagsInDropdown();
    
    // Render time config
    renderTimeConfig();
}

// === RENDER TAGS IN DROPDOWN ===
function renderTagsInDropdown() {
    const container = document.getElementById('tagSelectionArea');
    
    if (!container) {
        console.error("tagSelectionArea not found in HTML!");
        return;
    }
    
    // Clear
    container.innerHTML = '';
    
    // Lấy tags (ưu tiên cache, fallback default)
    const tags = cachedTags.length > 0 ? cachedTags : AVAILABLE_TAGS;
    const activeTags = currentConfig.preferred_tags || [];
    
    console.log("Rendering tags:", tags);
    
    if (tags.length === 0) {
        container.innerHTML = '<p style="color: #999; padding: 8px;">Không có tags</p>';
        return;
    }
    
    // Render each tag
    tags.forEach(tag => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `tag-btn${activeTags.includes(tag) ? ' active' : ''}`;
        btn.textContent = tag;
        btn.dataset.tag = tag;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            btn.classList.toggle('active');
            updateTagsText();
        });
        
        container.appendChild(btn);
    });
    
    // Update display text
    updateTagsText();
    
    console.log("Rendered", tags.length, "tags");
}

// === UPDATE TAGS TEXT ===
function updateTagsText() {
    const textEl = document.getElementById('tagsSelectedText');
    if (!textEl) return;
    
    const selected = document.querySelectorAll('#tagSelectionArea .tag-btn.active');
    const count = selected.length;
    
    if (count === 0) {
        textEl.textContent = 'Chọn phong cách du lịch...';
        textEl.classList.remove('has-selection');
    } else if (count <= 3) {
        textEl.textContent = Array.from(selected).map(b => b.textContent).join(', ');
        textEl.classList.add('has-selection');
    } else {
        textEl.textContent = `Đã chọn ${count} phong cách`;
        textEl.classList.add('has-selection');
    }
}

// === RENDER TIME CONFIG ===
function renderTimeConfig() {
    const container = document.getElementById('timeConfigContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    BLOCK_CONFIG.forEach(block => {
        const config = currentConfig[block.id] || { 
            enabled: true, 
            start: block.defaultStart, 
            end: block.defaultEnd 
        };
        
        const div = document.createElement('div');
        div.className = 'time-config-item';
        div.innerHTML = `
            <div class="config-icon ${block.iconClass || ''}">
                <i class="fa-solid ${block.icon}"></i>
            </div>
            <div class="config-info">
                <div class="config-label">${block.label}</div>
                <div class="time-inputs">
                    <input type="time" id="start_${block.id}" class="time-control" value="${config.start}">
                    <span class="time-sep">—</span>
                    <input type="time" id="end_${block.id}" class="time-control" value="${config.end}">
                </div>
            </div>
            <div class="toggle-switch">
                <input type="checkbox" id="toggle_${block.id}" class="toggle-input" ${config.enabled ? 'checked' : ''}/>
                <label for="toggle_${block.id}" class="toggle-slider"></label>
            </div>
        `;
        container.appendChild(div);
    });
}
function handleRemovePlace(blockId, itemIndex, placeName) {
    // Xác nhận trước khi xóa
    const confirmed = confirm(`Bạn có chắc muốn xóa "${placeName}" khỏi lịch trình?`);
    if (!confirmed) return;
    
    // Lấy ngày hiện tại đang xem
    const currentDay = generatedTripData[activeDayIndex];
    if (!currentDay || !currentDay.blocks || !currentDay.blocks[blockId]) {
        console.error("Không tìm thấy block:", blockId);
        return;
    }
    
    // Xóa item khỏi block
    const blockItems = currentDay.blocks[blockId];
    if (itemIndex >= 0 && itemIndex < blockItems.length) {
        const removedItem = blockItems.splice(itemIndex, 1)[0];
        
        console.log(`Đã xóa "${placeName}" khỏi ${blockId}`);
        
        // Lưu lại vào localStorage
        localStorage.setItem('trip', JSON.stringify(generatedTripData));
        
        // Render lại UI
        renderDayTimeline(currentDay, 'none', handleRemovePlace);
        renderHeaderInfo(currentConfig, generatedTripData);
        renderDayNavigator(generatedTripData, activeDayIndex, switchToDay);
        
        // Hiện thông báo
        showToast(`Đã xóa "${placeName}" khỏi lịch trình`);
    }
}

function showToast(message, duration = 3000) {
    // Xóa toast cũ nếu có
    const oldToast = document.querySelector('.toast-notification');
    if (oldToast) oldToast.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <i class="fa-solid fa-check-circle"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    // Animation show
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Tự động ẩn sau duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// === HANDLE CREATE TRIP ===
async function handleCreateTrip() {
    const btn = document.getElementById('btnCreateTrip');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang tạo...';
    }
    
    try {
        const formData = collectFormData();
        updateConfig(formData);
        
        console.log("Sending request:", formData);
        
        const result = await tripRecommand(formData);
        
        console.log("API Response:", result);
        
        if (result?.data) {
            // Parse days một lần duy nhất
            let days = [];
            if (Array.isArray(result.data.days)) {
                days = result.data.days;
            } else if (result.data.days && typeof result.data.days === 'object') {
                days = Object.values(result.data.days);
            } else if (Array.isArray(result.data)) {
                days = result.data;
            }
            
            console.log("Parsed days:", days);
            console.log("Days count:", days.length);
            
            // Dùng cùng 1 biến cho tất cả
            generatedTripData = days;
            activeDayIndex = 0;
            
            // Lưu vào localStorage
            localStorage.setItem('trip', JSON.stringify(days));
            
            // Debug trước khi render
            console.log("Calling renderHeaderInfo with:", currentConfig, generatedTripData);
            
            // Render với cùng 1 data
            renderHeaderInfo(currentConfig, generatedTripData);
            renderDayNavigator(generatedTripData, activeDayIndex, switchToDay);
            
            if (generatedTripData.length > 0) {
                renderDayTimeline(generatedTripData[activeDayIndex], 'fade', handleRemovePlace);
            }
            
            toggleModal(false);
        } else {
            console.error("No data in response");
            alert("Không có dữ liệu trả về!");
        }
    } catch (error) {
        console.error("Create trip error:", error);
        alert("Có lỗi xảy ra: " + error.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Tạo Lịch Trình';
        }
    }
}

// === COLLECT FORM DATA ===
function collectFormData() {
    const selectedTags = document.querySelectorAll('#tagSelectionArea .tag-btn.active');
    const preferredTags = Array.from(selectedTags).map(btn => btn.dataset.tag);
    
    const data = {
        city: document.getElementById('inputCity')?.value || 'Hà Nội',
        start_date: document.getElementById('inputStartDate')?.value || getTodayDate(),
        num_days: parseInt(document.getElementById('inputNumDays')?.value) || 3,
        num_people: parseInt(document.getElementById('inputNumPeople')?.value) || 1,
        preferred_tags: preferredTags,
        user_id: currentUser ? currentUser.id : null  // ✅ THÊM: user_id
    };
    
    BLOCK_CONFIG.forEach(block => {
        data[block.id] = {
            enabled: document.getElementById(`toggle_${block.id}`)?.checked ?? true,
            start: document.getElementById(`start_${block.id}`)?.value || block.defaultStart,
            end: document.getElementById(`end_${block.id}`)?.value || block.defaultEnd
        };
    });
    
    return data;
}

// === HELPERS ===
function switchToDay(index) {
    if (index < 0 || index >= generatedTripData.length) return;
    activeDayIndex = index;
    renderDayNavigator(generatedTripData, activeDayIndex, switchToDay);
    //Truyền handleRemovePlace
    renderDayTimeline(generatedTripData[activeDayIndex], 'none', handleRemovePlace);
}

function getTodayDate() {
    return new Date().toISOString().split('T')[0];
}

// === EXPOSE TO GLOBAL ===
window.toggleModal = toggleModal;