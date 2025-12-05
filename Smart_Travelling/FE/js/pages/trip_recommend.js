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

// === INIT ===
document.addEventListener('DOMContentLoaded', () => init());

async function init() {
    console.log("🚀 Initializing...");
    
    // Fetch tags ngay khi load trang
    await fetchAndCacheTags();
    
    // Setup events
    setupModalEvents();
    setupTagsDropdown();
    
    // Render header mặc định
    renderHeaderInfo(currentConfig);
    
    console.log("✅ Init complete!");
}

// === FETCH TAGS ===
async function fetchAndCacheTags() {
    try {
        console.log("📡 Fetching tags from API...");
        const result = await getTags();
        console.log("📡 API Response:", result);
        
        // Xử lý các kiểu response khác nhau
        if (result && result.data && Array.isArray(result.data)) {
            cachedTags = result.data;
        } else if (Array.isArray(result)) {
            cachedTags = result;
        } else {
            console.warn("⚠️ Invalid response, using defaults");
            cachedTags = [...AVAILABLE_TAGS];
        }
        
        console.log("✅ Cached tags:", cachedTags);
        localStorage.setItem("tags", JSON.stringify(cachedTags));
        
    } catch (error) {
        console.error("❌ Fetch tags failed:", error);
        
        // Fallback
        const stored = localStorage.getItem("tags");
        cachedTags = stored ? JSON.parse(stored) : [...AVAILABLE_TAGS];
        console.log("📦 Using fallback tags:", cachedTags);
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
        console.warn("⚠️ Tags dropdown elements not found");
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
        console.log("📂 Opening modal...");
        
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
    console.log("🎨 Rendering form...");
    
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
        console.error("❌ #tagSelectionArea not found in HTML!");
        return;
    }
    
    // Clear
    container.innerHTML = '';
    
    // Lấy tags (ưu tiên cache, fallback default)
    const tags = cachedTags.length > 0 ? cachedTags : AVAILABLE_TAGS;
    const activeTags = currentConfig.preferred_tags || [];
    
    console.log("🏷️ Rendering tags:", tags);
    
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
    
    console.log("✅ Rendered", tags.length, "tags");
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
        
        const result = await tripRecommand(formData);
        
        if (result?.data) {
            generatedTripData = result.data.days || [];
            activeDayIndex = 0;
            
            renderHeaderInfo(currentConfig, result.data);
            renderDayNavigator(generatedTripData, activeDayIndex, switchToDay);
            renderDayTimeline(generatedTripData[activeDayIndex]);
            
            toggleModal(false);
        }
    } catch (error) {
        console.error("❌ Create trip error:", error);
        alert("Có lỗi xảy ra!");
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
        preferred_tags: preferredTags
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
    renderDayTimeline(generatedTripData[activeDayIndex]);
}

function getTodayDate() {
    return new Date().toISOString().split('T')[0];
}

// === EXPOSE TO GLOBAL ===
window.toggleModal = toggleModal;