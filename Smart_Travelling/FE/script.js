// ===== CẤU HÌNH API =====
const API_URL = 'http://localhost:8000/api/v0/places/search';

// ===== PHẦN 1: TÌM KIẾM BẢN ĐỒ =====
const mapSearchForm = document.getElementById('map-search-form');
const mapSearchInput = document.getElementById('map-search-input');
const foundAddress = document.getElementById('found-address');
const addressText = document.getElementById('address-text');
const googleMapIframe = document.getElementById('google-map-iframe');

// Xử lý tìm kiếm trên bản đồ
mapSearchForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const query = mapSearchInput.value.trim();
    
    if (query) {
        // Cập nhật iframe với địa điểm mới
        googleMapIframe.src = `https://www.google.com/maps?q=${encodeURIComponent(query)}&output=embed`;
        
        // Hiển thị địa chỉ tìm được
        addressText.textContent = query;
        foundAddress.classList.add('show');
    }
});

// ===== PHẦN 2: MODAL KHÁM PHÁ ĐIỂM ĐẾN =====
const exploreBtn = document.getElementById('explore-btn');
const exploreModal = document.getElementById('explore-modal');
const closeModal = document.getElementById('close-modal');
const destinationForm = document.getElementById('destination-search-form');
const destinationInput = document.getElementById('destination-input');
const loadingSpinner = document.getElementById('loading-spinner');
const resultsContainer = document.getElementById('results-container');
const pinAllContainer = document.getElementById('pin-all-container');
const pinAllBtn = document.getElementById('pin-all-btn');
const pinCount = document.getElementById('pin-count');
const paginationControls = document.getElementById('pagination-controls');
const prevPageBtn = document.getElementById('prev-page-btn');
const nextPageBtn = document.getElementById('next-page-btn');
const pageInfo = document.getElementById('page-info');

let currentDestinationData = []; // Lưu dữ liệu địa điểm hiện tại
let currentPage = 1; // Trang hiện tại
const ITEMS_PER_PAGE = 2; // Số địa điểm mỗi lần pin (thay đổi từ 3 → 2)

// Mở modal
exploreBtn.addEventListener('click', () => {
    exploreModal.classList.add('show');
    destinationInput.focus();
});

// Đóng modal
closeModal.addEventListener('click', () => {
    exploreModal.classList.remove('show');
});

// Đóng modal khi click bên ngoài
exploreModal.addEventListener('click', (e) => {
    if (e.target === exploreModal) {
        exploreModal.classList.remove('show');
    }
});

// ===== XỬ LÝ NÚT PIN TẤT CẢ =====
pinAllBtn.addEventListener('click', () => {
    if (currentDestinationData.length === 0) {
        return;
    }
    
    pinCurrentPagePlaces();
});

// Nút trang trước
prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        updatePagination();
        pinCurrentPagePlaces();
    }
});

// Nút trang sau
nextPageBtn.addEventListener('click', () => {
    const totalPages = Math.ceil(currentDestinationData.length / ITEMS_PER_PAGE);
    if (currentPage < totalPages) {
        currentPage++;
        updatePagination();
        pinCurrentPagePlaces();
    }
});

// Hàm pin địa điểm của trang hiện tại
function pinCurrentPagePlaces() {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const placesToPin = currentDestinationData.slice(startIndex, endIndex);
    
    if (placesToPin.length === 0) return;
    
    // Tính tọa độ trung tâm của địa điểm
    const lats = placesToPin.map(p => p.address.lat);
    const lngs = placesToPin.map(p => p.address.lng);
    
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    
    const centerLat = (minLat + maxLat) / 2;
    const centerLng = (minLng + maxLng) / 2;
    
    // Tính zoom level
    const latDiff = maxLat - minLat;
    const lngDiff = maxLng - minLng;
    const maxDiff = Math.max(latDiff, lngDiff);
    
    let zoomLevel = 15;
    if (maxDiff > 0.1) zoomLevel = 13;
    else if (maxDiff > 0.05) zoomLevel = 14;
    else if (maxDiff > 0.02) zoomLevel = 15;
    else zoomLevel = 16;
    
    // Tạo URL Google Maps với markers
    if (placesToPin.length === 1) {
        const place = placesToPin[0];
        googleMapIframe.src = `https://www.google.com/maps?q=${place.address.lat},${place.address.lng}&z=${zoomLevel}&output=embed`;
        addressText.textContent = `${place.name}`;
    } else {
        const origin = placesToPin[0];
        const dest = placesToPin[1];
        googleMapIframe.src = `https://www.google.com/maps/dir/${origin.address.lat},${origin.address.lng}/${dest.address.lat},${dest.address.lng}/?output=embed`;
        addressText.textContent = `${origin.name} → ${dest.name}`;
    }
    
    foundAddress.classList.add('show');
    exploreModal.classList.remove('show');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Hiển thị pagination controls
    paginationControls.style.display = 'flex';
    updatePagination();
    
    showNotification(`Đã pin ${placesToPin.length} địa điểm lên bản đồ (Trang ${currentPage})`);
}

// Cập nhật trạng thái pagination
function updatePagination() {
    const totalPages = Math.ceil(currentDestinationData.length / ITEMS_PER_PAGE);
    
    pageInfo.textContent = `${currentPage} / ${totalPages}`;
    
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage === totalPages;
    
    // Cập nhật text nút pin
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, currentDestinationData.length);
    const count = endIndex - startIndex;
    pinAllBtn.querySelector('span:nth-child(2)').textContent = `Pin ${count} địa điểm lên bản đồ`;
}

// ===== PHẦN 2.5: MODAL TÌM ĐƯỜNG ĐI =====
const routeBtn = document.getElementById('route-btn');
const routeModal = document.getElementById('route-modal');
const closeRouteModal = document.getElementById('close-route-modal');
const originInput = document.getElementById('origin-input');
const destinationInputRoute = document.getElementById('destination-input-route');
const swapPointsBtn = document.getElementById('swap-points-btn');
const findRouteBtn = document.getElementById('find-route-btn');
const suggestionsList = document.getElementById('suggestions-list');

let currentPlaces = []; // Lưu danh sách địa điểm từ API
let selectedOrigin = null;
let selectedDestination = null;

// Mở modal tìm đường
routeBtn.addEventListener('click', async () => {
    routeModal.classList.add('show');
    originInput.focus();
    
    // Load danh sách địa điểm gợi ý (lấy từ Hồ Chí Minh mặc định)
    if (currentPlaces.length === 0) {
        await loadPlacesForRoute('Hồ Chí Minh');
    }
});

// Đóng modal
closeRouteModal.addEventListener('click', () => {
    routeModal.classList.remove('show');
});

// Đóng modal khi click bên ngoài
routeModal.addEventListener('click', (e) => {
    if (e.target === routeModal) {
        routeModal.classList.remove('show');
    }
});

// Đổi điểm đi/đến
swapPointsBtn.addEventListener('click', () => {
    const temp = originInput.value;
    originInput.value = destinationInputRoute.value;
    destinationInputRoute.value = temp;
    
    const tempSelected = selectedOrigin;
    selectedOrigin = selectedDestination;
    selectedDestination = tempSelected;
});

// Tìm đường
findRouteBtn.addEventListener('click', () => {
    const origin = originInput.value.trim();
    const destination = destinationInputRoute.value.trim();
    
    if (!origin || !destination) {
        alert('Vui lòng nhập đầy đủ điểm đi và điểm đến');
        return;
    }
    
    // Cập nhật iframe với tuyến đường
    googleMapIframe.src = `https://www.google.com/maps?saddr=${encodeURIComponent(origin)}&daddr=${encodeURIComponent(destination)}&output=embed`;
    
    // Hiển thị thông tin trên thanh search
    addressText.textContent = `${origin} → ${destination}`;
    foundAddress.classList.add('show');
    
    // Đóng modal
    routeModal.classList.remove('show');
});

// Load danh sách địa điểm từ API
async function loadPlacesForRoute(city) {
    try {
        const response = await fetch(`${API_URL}?province=${encodeURIComponent(city)}&limit=5`);
        const data = await response.json();
        
        if (data.success && data.places && data.places.length > 0) {
            currentPlaces = data.places;
            displaySuggestions(data.places);
        }
    } catch (error) {
        console.error('Error loading places:', error);
    }
}

// Hiển thị gợi ý địa điểm
function displaySuggestions(places) {
    suggestionsList.innerHTML = '';
    
    places.forEach(place => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.innerHTML = `
            <span class="material-icons">place</span>
            <div class="suggestion-info">
                <div class="suggestion-name">${place.name}</div>
                <div class="suggestion-address">${place.address.street}, ${place.address.district}</div>
            </div>
        `;
        
        // Click để chọn làm điểm đi hoặc điểm đến
        item.addEventListener('click', () => {
            const fullAddress = `${place.name}, ${place.address.street}, ${place.address.district}, ${place.address.city}`;
            
            // Nếu chưa có điểm đi, chọn làm điểm đi
            if (!originInput.value) {
                originInput.value = fullAddress;
                selectedOrigin = place;
            }
            // Nếu đã có điểm đi, chọn làm điểm đến
            else if (!destinationInputRoute.value) {
                destinationInputRoute.value = fullAddress;
                selectedDestination = place;
            }
            // Nếu đã đủ cả 2, thay thế điểm đến
            else {
                destinationInputRoute.value = fullAddress;
                selectedDestination = place;
            }
        });
        
        suggestionsList.appendChild(item);
    });
}

// ===== PHẦN 3: TÌM KIẾM ĐỊA ĐIỂM DU LỊCH (CALL API) =====
destinationForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('🔍 [DEBUG] Form submitted, prevented default');
    
    const destination = destinationInput.value.trim();
    console.log('🔍 [DEBUG] Destination:', destination);
    
    if (!destination) {
        showError('Vui lòng nhập tên tỉnh/thành phố');
        return;
    }
    
    // Hiện loading, xóa kết quả cũ
    loadingSpinner.classList.add('show');
    resultsContainer.innerHTML = '';
    console.log('🔍 [DEBUG] Starting API call...');
    
    try {
        // Call API với fetch
        console.log('🔍 [DEBUG] Fetching:', `${API_URL}?province=${encodeURIComponent(destination)}&limit=5`);
        const response = await fetch(`${API_URL}?province=${encodeURIComponent(destination)}&limit=5`);
        
        // Kiểm tra HTTP status
        if (!response.ok) {
            console.error('🔍 [DEBUG] HTTP Error:', response.status);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Parse JSON response
        console.log('🔍 [DEBUG] Response OK, parsing JSON...');
        const data = await response.json();
        console.log('🔍 [DEBUG] Data received:', data);
        
        // Debug: Log toàn bộ response
        console.log('📦 API Response:', data);
        console.log('📦 data.success:', data.success);
        console.log('📦 data.places:', data.places);
        console.log('📦 data.places?.length:', data.places?.length);
        
        // Ẩn loading
        loadingSpinner.classList.remove('show');
        
        // Kiểm tra success từ Backend API
        if (!data.success) {
            // Hiển thị lỗi từ API
            showError(data.message || 'Có lỗi xảy ra khi tìm kiếm');
            return;
        }
        
        // Kiểm tra có dữ liệu không
        if (!data.places || data.places.length === 0) {
            showNoResults(destination);
            return;
        }
        
        // Hiển thị kết quả
        displayResults(data.places);
        
        // Lưu dữ liệu và hiển thị nút pin tất cả
        currentDestinationData = data.places;
        currentPage = 1; // Reset về trang 1
        const itemsOnFirstPage = Math.min(ITEMS_PER_PAGE, data.places.length);
        pinCount.textContent = data.places.length;
        pinAllBtn.querySelector('span:nth-child(2)').textContent = `Pin ${itemsOnFirstPage} địa điểm lên bản đồ`;
        pinAllContainer.style.display = 'block';
        paginationControls.style.display = 'none'; // Ẩn pagination ban đầu
        updatePagination();
        
    } catch (error) {
        // Ẩn loading
        loadingSpinner.classList.remove('show');
        
        // Xử lý các loại lỗi khác nhau
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('Không thể kết nối đến server. Vui lòng kiểm tra server có đang chạy không.');
        } else {
            showError(`Lỗi: ${error.message}`);
        }
        
        console.error('Error calling API:', error);
    }
});

// ===== PHẦN 4: HIỂN THỊ KẾT QUẢ =====
function displayResults(data) {
    resultsContainer.innerHTML = '';
    
    console.log('🎨 Rendering', data.length, 'places');
    
    data.forEach(place => {
        const card = document.createElement('div');
        card.className = 'result-item';
        
        // Build address string (handle null values)
        let addressParts = [];
        if (place.address?.street) addressParts.push(place.address.street);
        if (place.address?.ward) addressParts.push(place.address.ward);
        if (place.address?.district) addressParts.push(place.address.district);
        if (place.address?.city) addressParts.push(place.address.city);
        const addressStr = addressParts.length > 0 ? addressParts.join(', ') : 'Chưa có địa chỉ';
        
        // Build time string
        const timeStr = (place.openTime && place.closeTime) 
            ? `${place.openTime} - ${place.closeTime}` 
            : 'Chưa có thông tin giờ mở cửa';
        
        // Xây dựng HTML cho địa điểm
        card.innerHTML = `
            <img 
                src="${place.imageLocalPath || 'https://via.placeholder.com/120x120?text=No+Image'}" 
                alt="${place.name}"
                class="result-image"
                onerror="this.src='https://via.placeholder.com/120x120?text=No+Image'"
            >
            <div class="result-info">
                <div class="result-header">
                    <h3 class="result-name">${place.name}</h3>
                    ${place.rating ? `
                        <div class="result-rating">
                            <span class="material-icons">star</span>
                            <span>${place.rating.toFixed(1)}</span>
                        </div>
                    ` : ''}
                </div>
                
                <div class="result-meta">
                    ${place.reviewCount ? `
                        <span>
                            <span class="material-icons">people</span>
                            ${formatNumber(place.reviewCount)} đánh giá
                        </span>
                    ` : ''}
                    ${place.priceVnd ? `
                        <span>
                            <span class="material-icons">payments</span>
                            ${formatPrice(place.priceVnd)}
                        </span>
                    ` : ''}
                    <span>
                        <span class="material-icons">schedule</span>
                        ${timeStr}
                    </span>
                </div>
                
                <p class="result-summary">${place.summary || place.description || 'Địa điểm du lịch tại ' + (place.address?.city || 'Việt Nam')}</p>
                
                <div class="result-footer">
                    <div class="result-address">
                        <span class="material-icons">location_on</span>
                        <span>${addressStr}</span>
                    </div>
                    ${place.address?.url ? `
                        <button class="open-maps-btn" data-url="${place.address.url}" title="Mở Google Maps">
                            <span class="material-icons">open_in_new</span>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Nút mở Google Maps (không đóng modal)
        const openMapsBtn = card.querySelector('.open-maps-btn');
        if (openMapsBtn) {
            openMapsBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Ngăn event click của card
                window.open(place.address.url, '_blank');
            });
        }
        
        // Click vào card để pin địa điểm lên bản đồ
        card.addEventListener('click', () => {
            // Pin địa điểm lên bản đồ Google Maps
            if (place.address?.lat && place.address?.lng) {
                googleMapIframe.src = `https://www.google.com/maps?q=${place.address.lat},${place.address.lng}&z=16&output=embed`;
                
                // Hiển thị tên địa điểm trên thanh search
                addressText.textContent = `${place.name}`;
                foundAddress.classList.add('show');
                
                // Đóng modal và cuộn lên đầu trang
                exploreModal.classList.remove('show');
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
        
        resultsContainer.appendChild(card);
    });
}

// ===== PHẦN 5: HIỂN THỊ LỖI =====
function showError(message) {
    resultsContainer.innerHTML = `
        <div class="error-message">
            <span class="material-icons">error_outline</span>
            <div>
                <p><strong>Có lỗi xảy ra</strong></p>
                <p>${message}</p>
            </div>
        </div>
    `;
}

// ===== PHẦN 6: HIỂN THỊ KHÔNG CÓ KẾT QUẢ =====
function showNoResults(city) {
    resultsContainer.innerHTML = `
        <div class="no-results">
            <span class="material-icons">location_off</span>
            <h3>Không tìm thấy địa điểm</h3>
            <p>Không có kết quả cho "${city}". Vui lòng thử tìm kiếm khác.</p>
        </div>
    `;
}

// ===== HÀM HỖ TRỢ =====
// Format số với dấu phẩy (10000 -> 10,000)
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Format giá tiền VND (50000 -> 50.000đ)
function formatPrice(price) {
    return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "đ";
}

// Hiển thị notification tạm thời
function showNotification(message) {
    // Tạo element notification
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <span class="material-icons">info</span>
        <span>${message}</span>
    `;
    
    // Thêm vào body
    document.body.appendChild(notification);
    
    // Hiển thị với animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Tự động ẩn sau 3 giây
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Hiển thị notification với nút action
function showNotificationWithAction(message, buttonText, onClickAction) {
    // Tạo element notification
    const notification = document.createElement('div');
    notification.className = 'notification notification-action';
    notification.innerHTML = `
        <span class="material-icons">info</span>
        <span class="notification-message">${message}</span>
        <button class="notification-btn">${buttonText}</button>
    `;
    
    // Thêm vào body
    document.body.appendChild(notification);
    
    // Xử lý click button
    const btn = notification.querySelector('.notification-btn');
    btn.addEventListener('click', () => {
        onClickAction();
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    });
    
    // Hiển thị với animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Tự động ẩn sau 8 giây (lâu hơn vì có button)
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 8000);
}
