# app/domain/entities/visitor_entity.py

# Mình import mấy kiểu dữ liệu cần dùng
from typing import List, Set, Optional  # List: danh sách, Set: tập hợp không trùng, Optional: có thể None
import random                          # dùng để random địa điểm
from .place_lite import PlaceLite      # import model PlaceLite (dữ liệu địa điểm) để type-hint cho rõ

class VisitorEntity:
    """
    Entity này mình tạo ra để lo riêng phần gợi ý cho visitor.
    Nó KHÔNG phải model DB, chỉ là lớp xử lý thuật toán.
    
    Nhiệm vụ:
    - random ra 5 địa điểm
    - refresh thì tránh lặp lại những chỗ đã gợi ý trước đó
    """

    def __init__(self, places: List[PlaceLite]):
        # Hàm khởi tạo (constructor).
        # places là danh sách địa điểm theo city mà mình lấy từ DB lên rồi.
        # Mình lưu nó vào self.places để các hàm khác trong class dùng lại.
        self.places = places

    def recommend_no_repeat(self, seen_ids: Optional[Set[int]] = None, k: int = 5) -> List[PlaceLite]:
        """
        Hàm chính để gợi ý địa điểm.

        - Trả về k địa điểm random nhưng KHÔNG trùng với tập seen_ids.
        - seen_ids là các id đã gợi ý trước đó (client gửi lên).
        - Nếu seen_ids None => coi như lần đầu vào => chưa xem gì cả.
        - Nếu số địa điểm còn lại < k => mình reset seen_ids để random lại từ đầu.
        """

        # Nếu list địa điểm rỗng (DB không có gì) thì trả về danh sách rỗng luôn
        if not self.places:
            return []

        # Nếu client chưa gửi seen_ids (lần đầu) thì mình tạo set rỗng
        if seen_ids is None:
            seen_ids = set()

        # Tạo danh sách rỗng để chứa các địa điểm CHƯA seen
        remain = []

        # Duyệt từng địa điểm trong danh sách places
        for place in self.places:
            
            # Nếu id của place KHÔNG nằm trong seen_ids
            # nghĩa là visitor chưa được gợi ý chỗ này
            if place.id not in seen_ids:
                
                # thì thêm nó vào danh sách remain
                remain.append(place)


        # Nếu số địa điểm chưa thấy còn ít hơn k (vd: còn 2 chỗ mà k=5)
        # thì mình reset seen_ids để bắt đầu vòng random mới
        if len(remain) < k:
            seen_ids.clear()       # xóa hết id đã seen
            remain = self.places   # cho remain trở lại full list để random lại từ đầu

        # Random đều k địa điểm từ remain
        # min(k, len(remain)) để tránh lỗi nếu remain nhỏ hơn k
        sample = random.sample(remain, k=min(k, len(remain)))

        # Sau khi random xong, mình cập nhật lại seen_ids
        # để lần refresh sau sẽ né mấy chỗ này
        for p in sample:
            if p.id is not None:   # check chắc chắn có id
                seen_ids.add(p.id)  # add id vô set (set tự chống trùng)

        # Trả về danh sách địa điểm đã random
        return sample
