import { BLOCK_CONFIG } from "../services/trip.service.js";

// Hàm format tiền tệ
function formatCurrency(amount) {
    if (amount >= 1000000) {
        return (amount / 1000000).toFixed(1) + 'M';
    } else if (amount >= 1000) {
        return (amount / 1000).toFixed(0) + 'K';
    }
    return amount.toString();
}

// Hàm parse giá tiền từ string
function parsePrice(priceStr) {
    if (!priceStr) return 0;
    if (typeof priceStr === 'number') return priceStr;
    // Loại bỏ các ký tự không phải số
    const numStr = priceStr.toString().replace(/[^0-9]/g, '');
    return parseInt(numStr) || 0;
}

// Tính tổng chi phí của một ngày
function calculateDayCost(dayData) {
    if (!dayData || !dayData.blocks) return 0;
    
    let total = 0;
    Object.values(dayData.blocks).forEach(items => {
        if (Array.isArray(items)) {
            items.forEach(item => {
                total += parsePrice(item.price_vnd);
            });
        }
    });
    return total;
}

// Tính tổng chi phí toàn bộ chuyến đi
export function calculateTotalCost(days) {
    if (!Array.isArray(days)) return 0;
    return days.reduce((sum, day) => sum + calculateDayCost(day), 0);
}

// Đếm tổng số điểm đến
export function countTotalPlaces(days) {
    if (!Array.isArray(days)) return 0;
    let count = 0;
    days.forEach(day => {
        if (day.blocks) {
            Object.values(day.blocks).forEach(items => {
                if (Array.isArray(items)) {
                    count += items.length;
                }
            });
        }
    });
    return count;
}

// Render thông tin Header (Thành phố, Ngày, Tags)
export function renderHeaderInfo(config, days = null) {
    document.getElementById('displayCity').textContent = config.city;
    const dParts = config.start_date.split('-');
    document.getElementById('displayDate').textContent = `${dParts[2]}/${dParts[1]}/${dParts[0]}`;
    document.getElementById('displayDuration').textContent = `${config.num_days} Ngày`;
    
    // Cập nhật tổng chi phí và số điểm đến nếu có dữ liệu
    if (days) {
        const totalCost = calculateTotalCost(days);
        const totalPlaces = countTotalPlaces(days);
        
        const displayTotal = document.getElementById('displayTotal');
        const displayTotalCost = document.getElementById('displayTotalCost');
        
        if (displayTotal) displayTotal.textContent = totalPlaces;
        if (displayTotalCost) {
            // Format số tiền với dấu phẩy
            displayTotalCost.textContent = totalCost.toLocaleString('vi-VN');
        }
    }
}

// Render thanh điều hướng ngày (Day Navigator)
export function renderDayNavigator(dataOrDays, activeIndex, onDayClick) {

    const days = Array.isArray(dataOrDays)
        ? dataOrDays
        : (dataOrDays && Array.isArray(dataOrDays.days) ? dataOrDays.days : []);

    if (!days.length) {
        console.warn("Không có days để render");
        return;
    }

    const nav = document.getElementById('dayNavigator');
    if (!nav) {
        console.error('Không tìm thấy element #dayNavigator');
        return;
    }

    nav.innerHTML = '';
    console.log("days truyền vào renderDayNavigator:", days);

    days.forEach((day, index) => {
        if (index > 0) {
            const connector = document.createElement('div');
            connector.className = "step-connector";
            nav.appendChild(connector);
        }

        const isActive = index === activeIndex;
        const btn = document.createElement('div');
        btn.className = `step-pill ${isActive ? 'active' : ''}`;

        // Gán sự kiện click được truyền từ bên ngoài vào
        btn.onclick = () => {
            if (typeof onDayClick === 'function') {
                onDayClick(index);
            }
        };

        const dateText = day.date || day.date_str || ''; // tùy server trả về
        
        // Tính tổng chi phí ngày
        const dayCost = calculateDayCost(day);
        const formattedCost = formatCurrency(dayCost);

        btn.innerHTML = `
            <span class="step-label">Ngày ${index + 1}</span>
            <span class="step-date">${dateText}</span>
            <span class="step-cost">${formattedCost}</span>
        `;
        nav.appendChild(btn);

        // Tự động cuộn nút active ra giữa
        if (isActive) {
            setTimeout(() => {
                btn.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'center'
                });
            }, 100);
        }
    });
}


// Render nội dung chi tiết của một ngày (Timeline)
export function renderDayTimeline(dayData, direction = 'none') {
    const container = document.getElementById('timelineContainer');
    
    console.log("Rendering timeline for date:", dayData.date);

    // Animation logic
    container.classList.remove('animate-slide-right', 'animate-slide-left');
    void container.offsetWidth; // Force reflow
    
    if (direction === 'right') container.classList.add('animate-slide-right');
    else if (direction === 'left') container.classList.add('animate-slide-left');
    else {
        container.style.opacity = '0';
        setTimeout(() => container.style.opacity = '1', 50);
    }

    container.innerHTML = '';
    let hasContent = false;

    BLOCK_CONFIG.forEach(block => {
        const items = dayData.blocks[block.id];
        if (items && items.length > 0) {
            hasContent = true;
            
            // Session Header
            const sessionHeader = document.createElement('div');
            sessionHeader.className = "session-header";
            sessionHeader.innerHTML = `
                <div class="session-icon ${block.iconClass}">
                    <i class="fa-solid ${block.icon}" style="color:white;"></i>
                </div>
                <div class="session-title-wrapper">
                        <h2 class="session-title">${block.label}</h2>
                        <div class="session-line"></div>
                </div>
            `;
            container.appendChild(sessionHeader);

            items.forEach((item) => {
                // Travel Info
                if (item.travel_min > 0) {
                    const travelDiv = document.createElement('div');
                    travelDiv.className = "travel-info";
                    travelDiv.innerHTML = `
                        <div class="travel-line"></div>
                        <div class="travel-badge">
                            <i class="fa-solid fa-person-walking-luggage"></i>
                            <span>${item.travel_min} phút</span>
                            <div class="dot-divider"></div>
                            <span>${item.distance_km} km</span>
                        </div>
                    `;
                    container.appendChild(travelDiv);
                }

                // Card Item
                const wrapper = document.createElement('div');
                wrapper.className = "timeline-item-wrapper";
                
                const line = document.createElement('div');
                line.className = "timeline-line-vertical";
                wrapper.appendChild(line);

                const dot = document.createElement('div');
                dot.className = "timeline-dot";
                wrapper.appendChild(dot);

                let iconType = 'fa-location-dot';
                if(item.type === 'eat') iconType = 'fa-utensils';
                if(item.type === 'coffee') iconType = 'fa-mug-hot';

                const card = document.createElement('div');
                card.className = "card";
                card.innerHTML = `
                    <div class="card-img-wrapper">
                        <img src="${item.image_url}" class="card-img">
                    </div>
                    <div class="card-content">
                        <div class="card-header">
                            <div>
                                <div class="time-badge">
                                    ${item.start} - ${item.end}
                                </div>
                                <h3 class="card-title">${item.name}</h3>
                            </div>
                            <div class="card-icon">
                                <i class="fa-solid ${iconType}"></i>
                            </div>
                        </div>
                        <div class="card-meta">
                            <span class="card-meta-item"><i class="fa-regular fa-clock"></i> ${item.dwell_min}</span>
                            <span class="card-meta-item"><i class="fa-solid fa-money-bill-1-wave"></i> ${item.price_vnd}</span>
                        </div>
                    </div>
                `;
                wrapper.appendChild(card);
                container.appendChild(wrapper);
            });
        }
    });

    if (!hasContent) container.innerHTML = `<div class="empty-state"><p>Không có hoạt động nào trong ngày này.</p></div>`;
}