#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DiningPlaceRepository: Quản lý các địa điểm ăn uống (nhà hàng, quán ăn, food court)
Chức năng:
- CRUD operations cho dining places
- Tìm kiếm theo tên, loại hình, giá cả, rating
- Lọc theo khoảng cách, giờ mở cửa
- Hybrid storage: MySQL primary, in-memory fallback
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import mysql.connector
from mysql.connector import Error

from entities.dining_place_model import DiningPlace
from models import Address
from normalize_text import normalize_text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _conn() -> Optional[mysql.connector.connection.MySQLConnection]:
    """
    Tạo kết nối đến MySQL database
    Returns: MySQL connection object hoặc None nếu thất bại
    """
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'travel'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        logger.info("MySQL connector imported successfully")
        return connection
    except Error as e:
        logger.error(f"MySQL connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


class DiningPlaceRepository:
    """
    Repository quản lý DiningPlace với hybrid storage:
    - Primary: MySQL database (persistent)
    - Fallback: In-memory dictionary (session only)
    """
    
    def __init__(self):
        """Khởi tạo repository với hybrid storage"""
        self.use_mysql = _conn() is not None
        self._in_memory_store: Dict[int, DiningPlace] = {}
        self._next_id = 1
        logger.info(f"DiningPlaceRepository initialized. Using MySQL: {self.use_mysql}")
    
    def save_dining_place(self, dining_place: DiningPlace) -> int:
        """
        Lưu dining place mới vào database/memory
        
        Chức năng:
        - Validate dữ liệu dining place qua Pydantic model
        - Lưu address trước (nếu có) để lấy address_id
        - Insert dining place vào table với normalized_name để hỗ trợ tìm kiếm
        - Tự động fallback sang in-memory nếu MySQL lỗi
        
        Args:
            dining_place: DiningPlace object cần lưu
                - name (str): Tên địa điểm - REQUIRED
                - cuisineType (str): Loại món ăn (Vietnamese, Chinese, Japanese, etc.)
                - priceRangeVnd (int): Giá trung bình một món (VNĐ)
                - summary (str): Mô tả ngắn
                - description (str): Mô tả chi tiết
                - openTime (str): Giờ mở cửa (format: "HH:MM")
                - closeTime (str): Giờ đóng cửa (format: "HH:MM")
                - phone (str): Số điện thoại
                - rating (float): Đánh giá (0-5 sao)
                - reviewCount (int): Số lượng review
                - popularity (int): Độ phổ biến
                - imageName (str): URL hoặc tên file ảnh
                - hasParking (bool): Có chỗ đỗ xe không
                - hasWifi (bool): Có wifi không
                - hasDelivery (bool): Có giao hàng không
                - address (Address): Object chứa thông tin địa chỉ và tọa độ
        
        Returns:
            int: ID của dining place vừa được lưu (auto-increment từ MySQL hoặc manual từ memory)
        
        Raises:
            ValidationError: Nếu dữ liệu không hợp lệ (từ Pydantic)
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> place = DiningPlace(
            ...     name="Phở 24",
            ...     cuisineType="Vietnamese",
            ...     priceRangeVnd=50000,
            ...     rating=4.5
            ... )
            >>> place_id = repo.save_dining_place(place)
            >>> print(place_id)  # Output: 1
        """
        logger.debug(f"Saving dining place: {dining_place.name}")
        
        if self.use_mysql:
            return self._save_to_mysql(dining_place)
        else:
            return self._save_to_memory(dining_place)
    
    def _save_to_mysql(self, dining_place: DiningPlace) -> int:
        """
        Lưu dining place vào MySQL database (internal helper function)
        
        Chức năng:
        - INSERT dining place vào table dining_places
        - Tự động generate normalized_name từ name
        - Tự động set created_at và updated_at = NOW()
        - Trả về ID auto-increment sau khi insert
        
        Args:
            dining_place (DiningPlace): Object cần lưu
        
        Returns:
            int: ID của record vừa insert (lastrowid từ cursor)
        
        Raises:
            mysql.connector.Error: Nếu có lỗi MySQL (duplicate, constraint, etc.)
        
        Note:
            - Hàm này là PRIVATE, chỉ gọi từ save_dining_place()
            - Caller phải đảm bảo address_id đã được lưu trước
        """
        """Lưu dining place vào MySQL database"""
        conn = _conn()
        if not conn:
            logger.error("Cannot connect to MySQL")
            return self._save_to_memory(dining_place)
        
        try:
            cursor = conn.cursor()
            logger.debug(f"Connected to database: {conn.database}")
            
            # 1. Lưu address trước (nếu có)
            address_id = None
            if dining_place.address:
                addr = dining_place.address
                cursor.execute("""
                    INSERT INTO addresses (house_number, street, ward, district, city, lat, lng, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    addr.houseNumber, addr.street, addr.ward, addr.district,
                    addr.city, addr.lat, addr.lng, addr.url
                ))
                address_id = cursor.lastrowid
                logger.debug(f"Saved address with ID: {address_id}")
            
            # 2. Lưu dining place
            data = dining_place.to_json()
            cursor.execute("""
                INSERT INTO dining_places 
                (name, normalized_name, cuisine_type, price_range_vnd, 
                 summary, description, open_time, close_time, phone, 
                 rating, review_count, popularity, image_name, 
                 has_parking, has_wifi, has_delivery, address_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['name'],
                normalize_text(data['name']),
                data.get('cuisineType'),
                data.get('priceRangeVnd'),
                data.get('summary'),
                data.get('description'),
                data.get('openTime'),
                data.get('closeTime'),
                data.get('phone'),
                data.get('rating'),
                data.get('reviewCount', 0),
                data.get('popularity', 0),
                data.get('imageName'),
                data.get('hasParking', False),
                data.get('hasWifi', False),
                data.get('hasDelivery', False),
                address_id
            ))
            
            dining_place_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved dining place to MySQL with ID: {dining_place_id}")
            return dining_place_id
            
        except Error as e:
            logger.error(f"MySQL error while saving dining place: {e}")
            conn.rollback()
            return self._save_to_memory(dining_place)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def _save_to_memory(self, dining_place: DiningPlace) -> int:
        """
        Lưu dining place vào in-memory store (fallback khi MySQL không khả dụng)
        
        Chức năng:
        - Generate ID manual = max(existing IDs) + 1
        - Lưu vào dict self.dining_places với key = ID
        - Dùng khi MySQL connection thất bại
        
        Args:
            dining_place (DiningPlace): Object cần lưu
        
        Returns:
            int: ID vừa generate (bắt đầu từ 1)
        
        Note:
            - Hàm này là PRIVATE, chỉ gọi từ save_dining_place()
            - Data sẽ mất khi restart app (not persistent)
            - Chỉ dùng cho testing/development
        """
        """Lưu dining place vào in-memory store"""
        dining_place_id = self._next_id
        self._next_id += 1
        self._in_memory_store[dining_place_id] = dining_place
        logger.info(f"Saved dining place to memory with ID: {dining_place_id}")
        return dining_place_id
    
    def get_dining_place_by_id(self, dining_place_id: int) -> Optional[DiningPlace]:
        """
        Lấy thông tin chi tiết của một dining place theo ID
        
        Chức năng:
        - Truy vấn dining place từ MySQL với JOIN address để lấy đầy đủ thông tin
        - Convert row data sang DiningPlace object với đầy đủ fields
        - Fallback sang in-memory store nếu MySQL không khả dụng
        
        Args:
            dining_place_id (int): ID của dining place cần tìm (primary key)
        
        Returns:
            Optional[DiningPlace]: 
                - DiningPlace object với đầy đủ thông tin nếu tìm thấy
                - None nếu không tìm thấy dining place với ID này
        
        SQL Query:
            SELECT dp.*, a.* FROM dining_places dp
            LEFT JOIN addresses a ON dp.address_id = a.id
            WHERE dp.id = ?
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> place = repo.get_dining_place_by_id(1)
            >>> if place:
            ...     print(f"Tìm thấy: {place.name}")
            ...     print(f"Địa chỉ: {place.address.street if place.address else 'N/A'}")
            ... else:
            ...     print("Không tìm thấy")
        """
        if self.use_mysql:
            return self._get_from_mysql(dining_place_id)
        else:
            return self._in_memory_store.get(dining_place_id)
    
    def _get_from_mysql(self, dining_place_id: int) -> Optional[DiningPlace]:
        """Lấy dining place từ MySQL"""
        conn = _conn()
        if not conn:
            return self._in_memory_store.get(dining_place_id)
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT dp.*, 
                       a.house_number, a.street, a.ward, a.district, 
                       a.city, a.lat, a.lng, a.url
                FROM dining_places dp
                LEFT JOIN addresses a ON dp.address_id = a.id
                WHERE dp.id = %s
            """, (dining_place_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_dining_place(row)
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            return self._in_memory_store.get(dining_place_id)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def find_by_keyword(self, keyword: str, limit: int = 50) -> List[DiningPlace]:
        """
        Tìm kiếm dining places theo từ khóa (hỗ trợ tiếng Việt có dấu)
        
        Chức năng:
        - Normalize keyword để tìm kiếm không phân biệt dấu (hỗ trợ tiếng Việt)
        - Tìm trong 5 fields: normalized_name, name, cuisine_type, summary, description
        - Sắp xếp kết quả theo rating và popularity (cao nhất trước)
        - Sử dụng LIKE %keyword% để tìm kiếm partial match
        
        Args:
            keyword (str): Từ khóa tìm kiếm
                - VD: "pho", "phở", "cafe", "quán ăn ngon"
                - Tự động normalize để tìm "pho" cũng match "phở"
            limit (int, optional): Số lượng kết quả tối đa. Default = 50
        
        Returns:
            List[DiningPlace]: Danh sách dining places tìm được
                - Sắp xếp theo: rating DESC, popularity DESC
                - Trả về list rỗng [] nếu không tìm thấy
        
        SQL Query:
            SELECT dp.*, a.* FROM dining_places dp
            LEFT JOIN addresses a ON dp.address_id = a.id
            WHERE dp.normalized_name LIKE %keyword%
               OR dp.name LIKE %keyword%
               OR dp.cuisine_type LIKE %keyword%
               OR dp.summary LIKE %keyword%
               OR dp.description LIKE %keyword%
            ORDER BY dp.rating DESC, dp.popularity DESC
            LIMIT ?
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Tìm tất cả quán phở
            >>> pho_places = repo.find_by_keyword("pho")
            >>> for place in pho_places:
            ...     print(f"{place.name} - Rating: {place.rating}")
            
            >>> # Tìm quán Nhật
            >>> japanese = repo.find_by_keyword("japanese", limit=10)
            >>> print(f"Tìm thấy {len(japanese)} quán Nhật")
        """
        normalized_keyword = normalize_text(keyword)
        logger.info(f"Searching dining places with keyword: {keyword}")
        
        if self.use_mysql:
            return self._find_in_mysql(normalized_keyword, limit)
        else:
            return self._find_in_memory(normalized_keyword, limit)
    
    def _find_in_mysql(self, normalized_keyword: str, limit: int) -> List[DiningPlace]:
        """Tìm kiếm trong MySQL database"""
        conn = _conn()
        if not conn:
            return self._find_in_memory(normalized_keyword, limit)
        
        try:
            cursor = conn.cursor(dictionary=True)
            search_pattern = f"%{normalized_keyword}%"
            
            cursor.execute("""
                SELECT dp.*, 
                       a.house_number, a.street, a.ward, a.district,
                       a.city, a.lat, a.lng, a.url
                FROM dining_places dp
                LEFT JOIN addresses a ON dp.address_id = a.id
                WHERE dp.normalized_name LIKE %s
                   OR dp.name LIKE %s
                   OR dp.cuisine_type LIKE %s
                   OR dp.summary LIKE %s
                   OR dp.description LIKE %s
                ORDER BY dp.rating DESC, dp.popularity DESC
                LIMIT %s
            """, (search_pattern, search_pattern, search_pattern, 
                  search_pattern, search_pattern, limit))
            
            results = [self._row_to_dining_place(row) for row in cursor.fetchall()]
            logger.info(f"Found {len(results)} dining places in MySQL")
            return results
            
        except Error as e:
            logger.error(f"MySQL search error: {e}")
            return self._find_in_memory(normalized_keyword, limit)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def _find_in_memory(self, normalized_keyword: str, limit: int) -> List[DiningPlace]:
        """Tìm kiếm trong in-memory store"""
        results = []
        for dp in self._in_memory_store.values():
            if (normalized_keyword in normalize_text(dp.name) or
                normalized_keyword in normalize_text(dp.cuisineType or '') or
                normalized_keyword in normalize_text(dp.summary or '') or
                normalized_keyword in normalize_text(dp.description or '')):
                results.append(dp)
                if len(results) >= limit:
                    break
        
        # Sort by rating and popularity
        results.sort(key=lambda x: (x.rating or 0, x.popularity or 0), reverse=True)
        logger.info(f"Found {len(results)} dining places in memory")
        return results
    
    def find_by_cuisine_type(self, cuisine_type: str, limit: int = 50) -> List[DiningPlace]:
        """
        Lọc dining places theo loại món ăn/ẩm thực
        
        Chức năng:
        - Tìm kiếm chính xác hoặc partial match với cuisine_type
        - Normalize để hỗ trợ tiếng Việt có dấu
        - Sắp xếp theo rating và popularity
        
        Args:
            cuisine_type (str): Loại món ăn cần tìm
                - Vietnamese: Món Việt (phở, bún, cơm)
                - Chinese: Món Trung (dimsum, mì, cơm chiên)
                - Japanese: Món Nhật (sushi, ramen, tempura)
                - Korean: Món Hàn (kimbap, bulgogi, kimchi)
                - Western: Món Âu (steak, pasta, pizza)
                - Thai: Món Thái (tom yum, pad thai)
                - Indian: Món Ấn (curry, tandoori)
                - Fast Food: Đồ ăn nhanh (burger, fried chicken)
                - Vegetarian: Ăn chay
                - Seafood: Hải sản
                - BBQ: Nướng/lẩu
                - Dessert: Tráng miệng/đồ ngọt
            limit (int, optional): Số lượng kết quả tối đa. Default = 50
        
        Returns:
            List[DiningPlace]: Danh sách dining places theo loại món ăn
                - Sắp xếp: rating DESC, popularity DESC
                - [] nếu không tìm thấy
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> vietnamese = repo.find_by_cuisine_type("Vietnamese")
            >>> print(f"Có {len(vietnamese)} quán Việt")
            
            >>> japanese = repo.find_by_cuisine_type("Japanese", limit=10)
            >>> top_japanese = japanese[0]
            >>> print(f"Top quán Nhật: {top_japanese.name} - {top_japanese.rating}⭐")
        """
        normalized_cuisine = normalize_text(cuisine_type)
        logger.info(f"Searching dining places by cuisine: {cuisine_type}")
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    WHERE dp.cuisine_type LIKE %s
                    ORDER BY dp.rating DESC, dp.popularity DESC
                    LIMIT %s
                """, (f"%{normalized_cuisine}%", limit))
                
                return [self._row_to_dining_place(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [dp for dp in self._in_memory_store.values() 
                      if normalized_cuisine in normalize_text(dp.cuisineType or '')]
            results.sort(key=lambda x: (x.rating or 0, x.popularity or 0), reverse=True)
            return results[:limit]
    
    def find_by_price_range(self, min_price: int, max_price: int, limit: int = 50) -> List[DiningPlace]:
        """
        Lọc dining places theo khoảng giá trung bình một món ăn
        
        Chức năng:
        - Tìm các dining place có price_range_vnd nằm trong khoảng [min_price, max_price]
        - Sắp xếp theo rating (cao nhất trước)
        - Hữu ích để tìm địa điểm phù hợp với budget
        
        Args:
            min_price (int): Giá tối thiểu (VNĐ)
                - VD: 20000 (20k VNĐ)
            max_price (int): Giá tối đa (VNĐ)
                - VD: 100000 (100k VNĐ)
            limit (int, optional): Số lượng kết quả tối đa. Default = 50
        
        Returns:
            List[DiningPlace]: Danh sách dining places trong khoảng giá
                - Sắp xếp: rating DESC
                - [] nếu không có địa điểm nào trong khoảng giá này
        
        SQL Query:
            SELECT dp.*, a.* FROM dining_places dp
            LEFT JOIN addresses a ON dp.address_id = a.id
            WHERE dp.price_range_vnd BETWEEN ? AND ?
            ORDER BY dp.rating DESC
            LIMIT ?
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Tìm quán giá rẻ (dưới 50k)
            >>> cheap = repo.find_by_price_range(0, 50000)
            >>> print(f"Có {len(cheap)} quán giá dưới 50k")
            
            >>> # Tìm quán trung bình (50k - 150k)
            >>> mid_range = repo.find_by_price_range(50000, 150000, limit=20)
            >>> for place in mid_range[:5]:
            ...     print(f"{place.name}: {place.priceRangeVnd:,}đ - {place.rating}⭐")
            
            >>> # Tìm quán cao cấp (trên 200k)
            >>> premium = repo.find_by_price_range(200000, 999999999)
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    WHERE dp.price_range_vnd BETWEEN %s AND %s
                    ORDER BY dp.rating DESC
                    LIMIT %s
                """, (min_price, max_price, limit))
                
                return [self._row_to_dining_place(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [dp for dp in self._in_memory_store.values()
                      if dp.priceRangeVnd and min_price <= dp.priceRangeVnd <= max_price]
            results.sort(key=lambda x: x.rating or 0, reverse=True)
            return results[:limit]
    
    def update_dining_place(self, dining_place: DiningPlace) -> bool:
        """
        Cập nhật thông tin của dining place đã tồn tại
        
        Chức năng:
        - Cập nhật tất cả fields của dining place (trừ ID và address_id)
        - Tự động normalize lại name khi update
        - Set updated_at = NOW() để track thời gian thay đổi
        - KHÔNG cập nhật address (phải dùng address repository riêng)
        
        Args:
            dining_place (DiningPlace): DiningPlace object với thông tin mới
                - MUST have id: ID của dining place cần update
                - Các fields khác sẽ được update theo giá trị mới
        
        Returns:
            bool: 
                - True: Cập nhật thành công
                - False: Thất bại (không tìm thấy ID hoặc lỗi MySQL)
        
        SQL Query:
            UPDATE dining_places SET
                name = ?, normalized_name = ?, cuisine_type = ?,
                price_range_vnd = ?, summary = ?, description = ?,
                open_time = ?, close_time = ?, phone = ?,
                rating = ?, review_count = ?, popularity = ?,
                image_name = ?, has_parking = ?, has_wifi = ?,
                has_delivery = ?, updated_at = NOW()
            WHERE id = ?
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Lấy dining place hiện tại
            >>> place = repo.get_dining_place_by_id(1)
            >>> if place:
            ...     # Cập nhật rating mới
            ...     place.rating = 4.8
            ...     place.reviewCount = 150
            ...     place.summary = "Quán phở ngon nhất quận 1"
            ...     
            ...     # Lưu thay đổi
            ...     success = repo.update_dining_place(place)
            ...     if success:
            ...         print("Cập nhật thành công!")
            ...     else:
            ...         print("Cập nhật thất bại!")
        """
        if not dining_place.id:
            logger.error("Cannot update dining place without ID")
            return False
        
        if self.use_mysql:
            return self._update_in_mysql(dining_place)
        else:
            return self._update_in_memory(dining_place)
    
    def _update_in_mysql(self, dining_place: DiningPlace) -> bool:
        """Cập nhật dining place trong MySQL"""
        conn = _conn()
        if not conn:
            return self._update_in_memory(dining_place)
        
        try:
            cursor = conn.cursor()
            data = dining_place.to_json()
            
            cursor.execute("""
                UPDATE dining_places SET
                    name = %s, normalized_name = %s, cuisine_type = %s,
                    price_range_vnd = %s, summary = %s, description = %s,
                    open_time = %s, close_time = %s, phone = %s,
                    rating = %s, review_count = %s, popularity = %s,
                    image_name = %s, has_parking = %s, has_wifi = %s,
                    has_delivery = %s, updated_at = NOW()
                WHERE id = %s
            """, (
                data['name'], normalize_text(data['name']), data.get('cuisineType'),
                data.get('priceRangeVnd'), data.get('summary'), data.get('description'),
                data.get('openTime'), data.get('closeTime'), data.get('phone'),
                data.get('rating'), data.get('reviewCount'), data.get('popularity'),
                data.get('imageName'), data.get('hasParking'), data.get('hasWifi'),
                data.get('hasDelivery'), dining_place.id
            ))
            
            conn.commit()
            logger.info(f"Updated dining place ID: {dining_place.id}")
            return True
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            conn.rollback()
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def _update_in_memory(self, dining_place: DiningPlace) -> bool:
        """Cập nhật dining place trong memory"""
        if dining_place.id in self._in_memory_store:
            self._in_memory_store[dining_place.id] = dining_place
            return True
        return False
    
    def delete_dining_place(self, dining_place_id: int) -> bool:
        """
        Xóa vĩnh viễn một dining place khỏi database
        
        Chức năng:
        - Xóa dining place từ table dining_places
        - WARNING: Không xóa address liên quan (phải xóa manual)
        - WARNING: Nên check foreign key constraints trước khi xóa
          (nếu có meal_options, meal_slots liên kết thì sẽ lỗi)
        
        Args:
            dining_place_id (int): ID của dining place cần xóa
        
        Returns:
            bool:
                - True: Xóa thành công
                - False: Xóa thất bại (không tìm thấy ID hoặc lỗi constraint)
        
        SQL Query:
            DELETE FROM dining_places WHERE id = ?
        
        Lưu ý:
            - Nên xóa tất cả meal_options liên quan trước
            - Nên xóa tất cả meal_slots liên quan trước
            - Hoặc set ON DELETE CASCADE trong schema
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Xóa dining place
            >>> success = repo.delete_dining_place(999)
            >>> if success:
            ...     print("Đã xóa thành công")
            ... else:
            ...     print("Không tìm thấy hoặc có lỗi")
            
            >>> # Best practice: Check trước khi xóa
            >>> place = repo.get_dining_place_by_id(1)
            >>> if place:
            ...     confirm = input(f"Xóa '{place.name}'? (y/n): ")
            ...     if confirm.lower() == 'y':
            ...         repo.delete_dining_place(1)
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM dining_places WHERE id = %s", (dining_place_id,))
                conn.commit()
                logger.info(f"Deleted dining place ID: {dining_place_id}")
                return cursor.rowcount > 0
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return False
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            if dining_place_id in self._in_memory_store:
                del self._in_memory_store[dining_place_id]
                return True
            return False
    
    def _row_to_dining_place(self, row: Tuple) -> DiningPlace:
        """
        Convert MySQL row tuple thành DiningPlace object
        
        Chức năng:
        - Map các columns từ JOIN query (dining_places + addresses)
        - Parse address fields thành Address object (nếu có)
        - Convert NULL values thành None hoặc default values
        - Parse boolean từ TINYINT(1) trong MySQL
        
        Args:
            row (Tuple): Row data từ cursor.fetchone() hoặc cursor.fetchall()
                Expected columns (33 fields):
                [0-16]: dining_places columns (id, name, normalized_name, ...)
                [17-32]: addresses columns (id, street, ward, district, ...)
        
        Returns:
            DiningPlace: Object với đầy đủ fields và nested Address object
        
        Note:
            - Hàm này là PRIVATE, chỉ gọi từ get/find methods
            - Row order phải match với SELECT query trong get_dining_place_by_id()
        """
        """Convert MySQL row sang DiningPlace object"""
        address = None
        if row.get('lat') and row.get('lng'):
            address = Address(
                houseNumber=row.get('house_number'),
                street=row.get('street'),
                ward=row.get('ward'),
                district=row.get('district'),
                city=row.get('city'),
                lat=float(row['lat']),
                lng=float(row['lng']),
                url=row.get('url')
            )
        
        return DiningPlace(
            id=row['id'],
            name=row['name'],
            cuisineType=row.get('cuisine_type'),
            priceRangeVnd=row.get('price_range_vnd'),
            summary=row.get('summary'),
            description=row.get('description'),
            openTime=row.get('open_time'),
            closeTime=row.get('close_time'),
            phone=row.get('phone'),
            rating=float(row['rating']) if row.get('rating') else None,
            reviewCount=row.get('review_count', 0),
            popularity=row.get('popularity', 0),
            imageName=row.get('image_name'),
            hasParking=bool(row.get('has_parking', False)),
            hasWifi=bool(row.get('has_wifi', False)),
            hasDelivery=bool(row.get('has_delivery', False)),
            address=address
        )
    
    # ========================================
    # Advanced Filter Methods (Rating, Reviews, Popularity)
    # ========================================
    
    def find_by_rating(self, min_rating: float, max_rating: float = 5.0, limit: int = 50) -> List[DiningPlace]:
        """
        Lọc dining places theo khoảng rating (đánh giá)
        
        Chức năng:
        - Tìm các dining place có rating nằm trong khoảng [min_rating, max_rating]
        - Sắp xếp theo rating cao nhất trước
        - Hữu ích để tìm địa điểm chất lượng cao
        
        Args:
            min_rating (float): Rating tối thiểu (0-5 sao)
                - VD: 4.0 (chỉ lấy quán 4 sao trở lên)
            max_rating (float, optional): Rating tối đa. Default = 5.0
            limit (int, optional): Số lượng kết quả tối đa. Default = 50
        
        Returns:
            List[DiningPlace]: Danh sách dining places trong khoảng rating
                - Sắp xếp: rating DESC, review_count DESC
                - [] nếu không có địa điểm nào
        
        SQL Query:
            SELECT dp.*, a.* FROM dining_places dp
            LEFT JOIN addresses a ON dp.address_id = a.id
            WHERE dp.rating BETWEEN ? AND ?
            ORDER BY dp.rating DESC, dp.review_count DESC
            LIMIT ?
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Tìm quán đánh giá cao (4 sao trở lên)
            >>> top_rated = repo.find_by_rating(4.0)
            >>> print(f"Có {len(top_rated)} quán 4 sao trở lên")
            
            >>> # Tìm quán xuất sắc (4.5+ sao)
            >>> excellent = repo.find_by_rating(4.5, 5.0, limit=10)
            >>> for place in excellent:
            ...     print(f"{place.name}: {place.rating}⭐ ({place.reviewCount} reviews)")
        """
        logger.info(f"Filtering by rating: {min_rating} - {max_rating}")
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    WHERE dp.rating BETWEEN %s AND %s
                    ORDER BY dp.rating DESC, dp.review_count DESC
                    LIMIT %s
                """, (min_rating, max_rating, limit))
                
                results = [self._row_to_dining_place(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(results)} dining places with rating {min_rating}-{max_rating}")
                return results
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [dp for dp in self._in_memory_store.values()
                      if dp.rating and min_rating <= dp.rating <= max_rating]
            results.sort(key=lambda x: (x.rating or 0, x.reviewCount or 0), reverse=True)
            return results[:limit]
    
    def find_by_review_count(self, min_reviews: int, limit: int = 50) -> List[DiningPlace]:
        """
        Lọc dining places theo số lượng reviews (đánh giá)
        
        Chức năng:
        - Tìm các dining place có số lượng reviews >= min_reviews
        - Sắp xếp theo review_count cao nhất trước
        - Hữu ích để tìm địa điểm được nhiều người biết đến và đánh giá
        
        Args:
            min_reviews (int): Số lượng reviews tối thiểu
                - VD: 50 (chỉ lấy quán có ít nhất 50 reviews)
            limit (int, optional): Số lượng kết quả tối đa. Default = 50
        
        Returns:
            List[DiningPlace]: Danh sách dining places có đủ reviews
                - Sắp xếp: review_count DESC, rating DESC
                - [] nếu không có địa điểm nào
        
        SQL Query:
            SELECT dp.*, a.* FROM dining_places dp
            LEFT JOIN addresses a ON dp.address_id = a.id
            WHERE dp.review_count >= ?
            ORDER BY dp.review_count DESC, dp.rating DESC
            LIMIT ?
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Tìm quán được review nhiều (50+ reviews)
            >>> well_reviewed = repo.find_by_review_count(50)
            >>> print(f"Có {len(well_reviewed)} quán có 50+ reviews")
            
            >>> # Tìm quán phổ biến (100+ reviews)
            >>> popular = repo.find_by_review_count(100, limit=20)
            >>> top = popular[0]
            >>> print(f"Top: {top.name} - {top.reviewCount} reviews, {top.rating}⭐")
        """
        logger.info(f"Filtering by review count >= {min_reviews}")
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    WHERE dp.review_count >= %s
                    ORDER BY dp.review_count DESC, dp.rating DESC
                    LIMIT %s
                """, (min_reviews, limit))
                
                results = [self._row_to_dining_place(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(results)} dining places with {min_reviews}+ reviews")
                return results
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [dp for dp in self._in_memory_store.values()
                      if (dp.reviewCount or 0) >= min_reviews]
            results.sort(key=lambda x: (x.reviewCount or 0, x.rating or 0), reverse=True)
            return results[:limit]
    
    def find_by_popularity(self, min_popularity: int, limit: int = 50) -> List[DiningPlace]:
        """
        Lọc dining places theo độ phổ biến/nổi tiếng
        
        Chức năng:
        - Tìm các dining place có popularity >= min_popularity
        - Sắp xếp theo popularity cao nhất trước
        - Popularity = metric tổng hợp (views, shares, bookmarks, etc.)
        
        Args:
            min_popularity (int): Độ phổ biến tối thiểu
                - VD: 1000 (chỉ lấy quán có độ phổ biến >= 1000)
            limit (int, optional): Số lượng kết quả tối đa. Default = 50
        
        Returns:
            List[DiningPlace]: Danh sách dining places phổ biến
                - Sắp xếp: popularity DESC, rating DESC
                - [] nếu không có địa điểm nào
        
        SQL Query:
            SELECT dp.*, a.* FROM dining_places dp
            LEFT JOIN addresses a ON dp.address_id = a.id
            WHERE dp.popularity >= ?
            ORDER BY dp.popularity DESC, dp.rating DESC
            LIMIT ?
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Tìm quán nổi tiếng (popularity >= 5000)
            >>> famous = repo.find_by_popularity(5000)
            >>> print(f"Có {len(famous)} quán nổi tiếng")
            
            >>> # Top 10 quán hot nhất
            >>> trending = repo.find_by_popularity(0, limit=10)
            >>> for i, place in enumerate(trending, 1):
            ...     print(f"{i}. {place.name} - Popularity: {place.popularity}")
        """
        logger.info(f"Filtering by popularity >= {min_popularity}")
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    WHERE dp.popularity >= %s
                    ORDER BY dp.popularity DESC, dp.rating DESC
                    LIMIT %s
                """, (min_popularity, limit))
                
                results = [self._row_to_dining_place(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(results)} dining places with popularity >= {min_popularity}")
                return results
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [dp for dp in self._in_memory_store.values()
                      if (dp.popularity or 0) >= min_popularity]
            results.sort(key=lambda x: (x.popularity or 0, x.rating or 0), reverse=True)
            return results[:limit]
    
    def get_top_rated(self, limit: int = 10) -> List[DiningPlace]:
        """
        Lấy danh sách top dining places có rating cao nhất
        
        Chức năng:
        - Trả về các dining place với rating cao nhất (4.5+ sao)
        - Chỉ lấy những quán có ít nhất 10 reviews để đảm bảo độ tin cậy
        - Sắp xếp theo rating DESC, sau đó theo review_count DESC
        
        Args:
            limit (int, optional): Số lượng kết quả. Default = 10
        
        Returns:
            List[DiningPlace]: Top dining places theo rating
                - Sắp xếp: rating DESC, review_count DESC
                - Chỉ lấy quán có rating >= 4.5 và reviewCount >= 10
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Top 10 quán ngon nhất
            >>> top10 = repo.get_top_rated(10)
            >>> for i, place in enumerate(top10, 1):
            ...     print(f"{i}. {place.name} - {place.rating}⭐ ({place.reviewCount} reviews)")
            
            >>> # Top 5 quán xuất sắc
            >>> top5 = repo.get_top_rated(5)
        """
        logger.info(f"Getting top {limit} rated dining places")
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    WHERE dp.rating >= 4.5 AND dp.review_count >= 10
                    ORDER BY dp.rating DESC, dp.review_count DESC
                    LIMIT %s
                """, (limit,))
                
                results = [self._row_to_dining_place(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(results)} top-rated dining places")
                return results
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [dp for dp in self._in_memory_store.values()
                      if (dp.rating or 0) >= 4.5 and (dp.reviewCount or 0) >= 10]
            results.sort(key=lambda x: (x.rating or 0, x.reviewCount or 0), reverse=True)
            return results[:limit]
    
    def get_most_popular(self, limit: int = 10) -> List[DiningPlace]:
        """
        Lấy danh sách dining places phổ biến nhất (trending)
        
        Chức năng:
        - Trả về các dining place có popularity cao nhất
        - Kết hợp với rating để đảm bảo chất lượng
        - Hữu ích để hiển thị "Trending Now" hoặc "Most Popular"
        
        Args:
            limit (int, optional): Số lượng kết quả. Default = 10
        
        Returns:
            List[DiningPlace]: Dining places phổ biến nhất
                - Sắp xếp: popularity DESC, rating DESC
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Top 10 quán hot nhất
            >>> trending = repo.get_most_popular(10)
            >>> for i, place in enumerate(trending, 1):
            ...     print(f"{i}. {place.name} - 🔥 {place.popularity} | {place.rating}⭐")
            
            >>> # Quán trending #1
            >>> hottest = repo.get_most_popular(1)[0]
            >>> print(f"Hottest place: {hottest.name}")
        """
        logger.info(f"Getting top {limit} most popular dining places")
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    ORDER BY dp.popularity DESC, dp.rating DESC
                    LIMIT %s
                """, (limit,))
                
                results = [self._row_to_dining_place(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(results)} most popular dining places")
                return results
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = list(self._in_memory_store.values())
            results.sort(key=lambda x: (x.popularity or 0, x.rating or 0), reverse=True)
            return results[:limit]
    
    def search_with_filters(
        self,
        keyword: Optional[str] = None,
        cuisine_type: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_rating: Optional[float] = None,
        min_reviews: Optional[int] = None,
        min_popularity: Optional[int] = None,
        has_parking: Optional[bool] = None,
        has_wifi: Optional[bool] = None,
        has_delivery: Optional[bool] = None,
        sort_by: str = "rating",  # rating | reviews | popularity | price
        limit: int = 50
    ) -> List[DiningPlace]:
        """
        Tìm kiếm và lọc dining places với nhiều điều kiện kết hợp
        
        Chức năng:
        - Tìm kiếm tổng hợp với nhiều filters cùng lúc
        - Sắp xếp theo nhiều tiêu chí: rating, reviews, popularity, price
        - Hỗ trợ filter theo amenities (parking, wifi, delivery)
        
        Args:
            keyword (str, optional): Từ khóa tìm kiếm
            cuisine_type (str, optional): Loại món ăn
            min_price (int, optional): Giá tối thiểu (VNĐ)
            max_price (int, optional): Giá tối đa (VNĐ)
            min_rating (float, optional): Rating tối thiểu (0-5)
            min_reviews (int, optional): Số reviews tối thiểu
            min_popularity (int, optional): Độ phổ biến tối thiểu
            has_parking (bool, optional): Phải có chỗ đỗ xe
            has_wifi (bool, optional): Phải có wifi
            has_delivery (bool, optional): Phải có giao hàng
            sort_by (str, optional): Sắp xếp theo (rating|reviews|popularity|price). Default = "rating"
            limit (int, optional): Số lượng kết quả. Default = 50
        
        Returns:
            List[DiningPlace]: Danh sách dining places thỏa mãn tất cả điều kiện
        
        Example:
            >>> repo = DiningPlaceRepository()
            >>> # Tìm quán Việt, giá rẻ, rating cao, có wifi
            >>> results = repo.search_with_filters(
            ...     cuisine_type="Vietnamese",
            ...     max_price=80000,
            ...     min_rating=4.0,
            ...     has_wifi=True,
            ...     sort_by="rating",
            ...     limit=20
            ... )
            
            >>> # Tìm quán hot, có giao hàng
            >>> trending = repo.search_with_filters(
            ...     min_popularity=5000,
            ...     has_delivery=True,
            ...     sort_by="popularity"
            ... )
        """
        logger.info(f"Advanced search with filters: keyword={keyword}, cuisine={cuisine_type}, "
                   f"price={min_price}-{max_price}, rating>={min_rating}, sort={sort_by}")
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Build WHERE conditions
                conditions = []
                params = []
                
                if keyword:
                    normalized_keyword = normalize_text(keyword)
                    conditions.append("""(dp.normalized_name LIKE %s OR dp.name LIKE %s 
                                       OR dp.cuisine_type LIKE %s OR dp.summary LIKE %s)""")
                    search_pattern = f"%{normalized_keyword}%"
                    params.extend([search_pattern] * 4)
                
                if cuisine_type:
                    conditions.append("dp.cuisine_type LIKE %s")
                    params.append(f"%{normalize_text(cuisine_type)}%")
                
                if min_price is not None:
                    conditions.append("dp.price_range_vnd >= %s")
                    params.append(min_price)
                
                if max_price is not None:
                    conditions.append("dp.price_range_vnd <= %s")
                    params.append(max_price)
                
                if min_rating is not None:
                    conditions.append("dp.rating >= %s")
                    params.append(min_rating)
                
                if min_reviews is not None:
                    conditions.append("dp.review_count >= %s")
                    params.append(min_reviews)
                
                if min_popularity is not None:
                    conditions.append("dp.popularity >= %s")
                    params.append(min_popularity)
                
                if has_parking is not None:
                    conditions.append("dp.has_parking = %s")
                    params.append(1 if has_parking else 0)
                
                if has_wifi is not None:
                    conditions.append("dp.has_wifi = %s")
                    params.append(1 if has_wifi else 0)
                
                if has_delivery is not None:
                    conditions.append("dp.has_delivery = %s")
                    params.append(1 if has_delivery else 0)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # Build ORDER BY
                order_map = {
                    "rating": "dp.rating DESC, dp.review_count DESC",
                    "reviews": "dp.review_count DESC, dp.rating DESC",
                    "popularity": "dp.popularity DESC, dp.rating DESC",
                    "price": "dp.price_range_vnd ASC"
                }
                order_by = order_map.get(sort_by, "dp.rating DESC")
                
                query = f"""
                    SELECT dp.*, 
                           a.house_number, a.street, a.ward, a.district,
                           a.city, a.lat, a.lng, a.url
                    FROM dining_places dp
                    LEFT JOIN addresses a ON dp.address_id = a.id
                    WHERE {where_clause}
                    ORDER BY {order_by}
                    LIMIT %s
                """
                
                params.append(limit)
                cursor.execute(query, params)
                
                results = [self._row_to_dining_place(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(results)} dining places matching filters")
                return results
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            # In-memory filtering
            results = list(self._in_memory_store.values())
            
            if keyword:
                normalized_keyword = normalize_text(keyword)
                results = [dp for dp in results if 
                          normalized_keyword in normalize_text(dp.name) or
                          normalized_keyword in normalize_text(dp.cuisineType or '') or
                          normalized_keyword in normalize_text(dp.summary or '')]
            
            if cuisine_type:
                normalized_cuisine = normalize_text(cuisine_type)
                results = [dp for dp in results if 
                          normalized_cuisine in normalize_text(dp.cuisineType or '')]
            
            if min_price is not None:
                results = [dp for dp in results if 
                          dp.priceRangeVnd and dp.priceRangeVnd >= min_price]
            
            if max_price is not None:
                results = [dp for dp in results if 
                          dp.priceRangeVnd and dp.priceRangeVnd <= max_price]
            
            if min_rating is not None:
                results = [dp for dp in results if 
                          (dp.rating or 0) >= min_rating]
            
            if min_reviews is not None:
                results = [dp for dp in results if 
                          (dp.reviewCount or 0) >= min_reviews]
            
            if min_popularity is not None:
                results = [dp for dp in results if 
                          (dp.popularity or 0) >= min_popularity]
            
            if has_parking is not None:
                results = [dp for dp in results if dp.hasParking == has_parking]
            
            if has_wifi is not None:
                results = [dp for dp in results if dp.hasWifi == has_wifi]
            
            if has_delivery is not None:
                results = [dp for dp in results if dp.hasDelivery == has_delivery]
            
            # Sort
            if sort_by == "rating":
                results.sort(key=lambda x: (x.rating or 0, x.reviewCount or 0), reverse=True)
            elif sort_by == "reviews":
                results.sort(key=lambda x: (x.reviewCount or 0, x.rating or 0), reverse=True)
            elif sort_by == "popularity":
                results.sort(key=lambda x: (x.popularity or 0, x.rating or 0), reverse=True)
            elif sort_by == "price":
                results.sort(key=lambda x: x.priceRangeVnd or 999999999)
            
            return results[:limit]
