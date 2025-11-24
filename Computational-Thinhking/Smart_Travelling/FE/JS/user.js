function switchTab(tabId, element) {
    // 1. Xóa class active ở tất cả menu
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    
    // 2. Thêm class active vào menu vừa bấm
    element.classList.add('active');

    // 3. Ẩn tất cả nội dung
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));

    // 4. Hiện nội dung tương ứng
    document.getElementById(tabId).classList.add('active');
}

function logout() {
    if(confirm('Bạn có chắc muốn đăng xuất không?')) {
        alert('Đã đăng xuất thành công!');
    }
}

// Giả lập nút Save
const saveBtns = document.querySelectorAll('.btn-primary');
saveBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        // Hiệu ứng button loading (giả lập)
        const originalText = btn.innerText;
        btn.innerText = 'Đang lưu...';
        btn.style.opacity = '0.7';
        
        setTimeout(() => {
            btn.innerText = originalText;
            btn.style.opacity = '1';
            alert('Đã cập nhật thông tin thành công!');
        }, 800);
    });
});