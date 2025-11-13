#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MealOptionRepository: Quản lý các món ăn/menu items
Chức năng:
- CRUD operations cho meal options (món ăn, đồ uống)
- Tìm kiếm theo tên món, loại món, giá cả
- Lọc theo dietary restrictions (vegetarian, halal, etc.)
- Link với DiningPlace
"""

import logging
from typing import List, Optional, Dict, Any
import mysql.connector
from mysql.connector import Error

from entities.meal_option_model import MealOption
from normalize_text import normalize_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _conn() -> Optional[mysql.connector.connection.MySQLConnection]:
    """Tạo kết nối MySQL"""
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
        return connection
    except Error as e:
        logger.error(f"MySQL connection error: {e}")
        return None


class MealOptionRepository:
    """Repository quản lý MealOption với hybrid storage"""
    
    def __init__(self):
        self.use_mysql = _conn() is not None
        self._in_memory_store: Dict[int, MealOption] = {}
        self._next_id = 1
        logger.info(f"MealOptionRepository initialized. Using MySQL: {self.use_mysql}")
    
    def save_meal_option(self, meal_option: MealOption) -> int:
        """
        Lưu meal option (món ăn) mới vào database/memory
        
        Chức năng:
        - Validate meal option data qua Pydantic model
        - INSERT vào table meal_options với normalized_name
        - Tự động fallback sang in-memory nếu MySQL lỗi
        
        Args:
            meal_option (MealOption): Object món ăn cần lưu
                - name (str): Tên món ăn - REQUIRED
                - diningPlaceId (int): ID của dining place - REQUIRED
                - category (str): Loại món (Appetizer, Main Course, Dessert, Beverage)
                - description (str): Mô tả món ăn
                - priceVnd (int): Giá tiền (VNĐ)
                - isVegetarian (bool): Có phải món chay không
                - isVegan (bool): Có phải món thuần chay không
                - isHalal (bool): Có phải món halal không
                - isGlutenFree (bool): Có phải món không gluten không
                - calories (int): Số calories
                - prepTimeMinutes (int): Thời gian chuẩn bị (phút)
                - spicyLevel (int): Độ cay (0-5, 0=không cay, 5=rất cay)
                - isAvailable (bool): Có còn phục vụ không
                - imageName (str): URL/tên file ảnh món ăn
        
        Returns:
            int: ID của meal option vừa lưu
        
        Example:
            >>> repo = MealOptionRepository()
            >>> meal = MealOption(
            ...     name="Phở bò tái",
            ...     diningPlaceId=1,
            ...     category="Main Course",
            ...     priceVnd=55000,
            ...     calories=450,
            ...     isAvailable=True
            ... )
            >>> meal_id = repo.save_meal_option(meal)
        """
        logger.debug(f"Saving meal option: {meal_option.name}")
        
        if self.use_mysql:
            return self._save_to_mysql(meal_option)
        else:
            return self._save_to_memory(meal_option)
    
    def _save_to_mysql(self, meal_option: MealOption) -> int:
        """Lưu meal option vào MySQL"""
        conn = _conn()
        if not conn:
            return self._save_to_memory(meal_option)
        
        try:
            cursor = conn.cursor()
            data = meal_option.to_json()
            
            cursor.execute("""
                INSERT INTO meal_options
                (dining_place_id, name, normalized_name, description,
                 price_vnd, category, is_vegetarian, is_vegan, is_halal,
                 is_gluten_free, calories, prep_time_minutes, image_name,
                 is_available, spicy_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('diningPlaceId'),
                data['name'],
                normalize_text(data['name']),
                data.get('description'),
                data.get('priceVnd'),
                data.get('category'),
                data.get('isVegetarian', False),
                data.get('isVegan', False),
                data.get('isHalal', False),
                data.get('isGlutenFree', False),
                data.get('calories'),
                data.get('prepTimeMinutes'),
                data.get('imageName'),
                data.get('isAvailable', True),
                data.get('spicyLevel', 0)
            ))
            
            meal_option_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved meal option to MySQL with ID: {meal_option_id}")
            return meal_option_id
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            conn.rollback()
            return self._save_to_memory(meal_option)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def _save_to_memory(self, meal_option: MealOption) -> int:
        """Lưu vào memory"""
        meal_option_id = self._next_id
        self._next_id += 1
        self._in_memory_store[meal_option_id] = meal_option
        logger.info(f"Saved meal option to memory with ID: {meal_option_id}")
        return meal_option_id
    
    def get_meal_option_by_id(self, meal_option_id: int) -> Optional[MealOption]:
        """Lấy meal option theo ID"""
        if self.use_mysql:
            return self._get_from_mysql(meal_option_id)
        else:
            return self._in_memory_store.get(meal_option_id)
    
    def _get_from_mysql(self, meal_option_id: int) -> Optional[MealOption]:
        """Lấy từ MySQL"""
        conn = _conn()
        if not conn:
            return self._in_memory_store.get(meal_option_id)
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM meal_options WHERE id = %s", (meal_option_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_meal_option(row)
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            return self._in_memory_store.get(meal_option_id)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def find_by_dining_place(self, dining_place_id: int) -> List[MealOption]:
        """
        Lấy tất cả meal options của một dining place
        Args:
            dining_place_id: ID của dining place
        Returns:
            List of MealOption
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_options 
                    WHERE dining_place_id = %s AND is_available = TRUE
                    ORDER BY category, name
                """, (dining_place_id,))
                
                return [self._row_to_meal_option(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            return [mo for mo in self._in_memory_store.values() 
                   if mo.diningPlaceId == dining_place_id and mo.isAvailable]
    
    def find_by_keyword(self, keyword: str, limit: int = 50) -> List[MealOption]:
        """
        Tìm kiếm meal options theo keyword (tên món, mô tả)
        """
        normalized_keyword = normalize_text(keyword)
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                search_pattern = f"%{normalized_keyword}%"
                
                cursor.execute("""
                    SELECT * FROM meal_options
                    WHERE (normalized_name LIKE %s OR description LIKE %s)
                      AND is_available = TRUE
                    ORDER BY name
                    LIMIT %s
                """, (search_pattern, search_pattern, limit))
                
                return [self._row_to_meal_option(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = []
            for mo in self._in_memory_store.values():
                if mo.isAvailable and (normalized_keyword in normalize_text(mo.name) or
                                      normalized_keyword in normalize_text(mo.description or '')):
                    results.append(mo)
                    if len(results) >= limit:
                        break
            return results
    
    def find_by_category(self, category: str, limit: int = 50) -> List[MealOption]:
        """
        Lọc món ăn theo danh mục/loại món
        
        Chức năng:
        - Tìm các món thuộc category cụ thể
        - Normalize để hỗ trợ tiếng Việt
        - Sắp xếp theo tên món
        
        Args:
            category (str): Loại món cần lọc
                - Appetizer: Khai vị (gỏi, salad, spring rolls)
                - Main Course: Món chính (cơm, phở, mì, steak)
                - Dessert: Tráng miệng (chè, kem, bánh ngọt)
                - Beverage: Đồ uống (nước, trà, cafe, smoothie)
                - Side Dish: Món phụ
                - Soup: Súp/canh
                - Snack: Đồ ăn vặt
            limit (int, optional): Số lượng kết quả. Default = 50
        
        Returns:
            List[MealOption]: Danh sách món theo category
                - Sắp xếp: name ASC
        
        Example:
            >>> repo = MealOptionRepository()
            >>> # Lấy tất cả món khai vị
            >>> appetizers = repo.find_by_category("Appetizer")
            >>> print(f"Có {len(appetizers)} món khai vị")
            
            >>> # Lấy đồ uống
            >>> drinks = repo.find_by_category("Beverage", limit=20)
            >>> for drink in drinks:
            ...     print(f"{drink.name}: {drink.calories} cal")
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_options
                    WHERE category = %s AND is_available = TRUE
                    ORDER BY name
                    LIMIT %s
                """, (category, limit))
                
                return [self._row_to_meal_option(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [mo for mo in self._in_memory_store.values()
                      if mo.category == category and mo.isAvailable]
            return results[:limit]
    
    def find_by_dietary_filter(self, 
                               is_vegetarian: bool = False,
                               is_vegan: bool = False,
                               is_halal: bool = False,
                               is_gluten_free: bool = False,
                               limit: int = 50) -> List[MealOption]:
        """
        Lọc meal options theo dietary restrictions
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                conditions = []
                params = []
                
                if is_vegetarian:
                    conditions.append("is_vegetarian = TRUE")
                if is_vegan:
                    conditions.append("is_vegan = TRUE")
                if is_halal:
                    conditions.append("is_halal = TRUE")
                if is_gluten_free:
                    conditions.append("is_gluten_free = TRUE")
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                cursor.execute(f"""
                    SELECT * FROM meal_options
                    WHERE {where_clause} AND is_available = TRUE
                    ORDER BY name
                    LIMIT %s
                """, (*params, limit))
                
                return [self._row_to_meal_option(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = []
            for mo in self._in_memory_store.values():
                if not mo.isAvailable:
                    continue
                if is_vegetarian and not mo.isVegetarian:
                    continue
                if is_vegan and not mo.isVegan:
                    continue
                if is_halal and not mo.isHalal:
                    continue
                if is_gluten_free and not mo.isGlutenFree:
                    continue
                results.append(mo)
                if len(results) >= limit:
                    break
            return results
    
    def find_by_price_range(self, min_price: int, max_price: int, limit: int = 50) -> List[MealOption]:
        """Tìm meal options theo khoảng giá"""
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_options
                    WHERE price_vnd BETWEEN %s AND %s AND is_available = TRUE
                    ORDER BY price_vnd
                    LIMIT %s
                """, (min_price, max_price, limit))
                
                return [self._row_to_meal_option(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [mo for mo in self._in_memory_store.values()
                      if mo.isAvailable and mo.priceVnd and min_price <= mo.priceVnd <= max_price]
            results.sort(key=lambda x: x.priceVnd or 0)
            return results[:limit]
    
    def update_meal_option(self, meal_option: MealOption) -> bool:
        """Cập nhật meal option"""
        if not meal_option.id:
            return False
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                data = meal_option.to_json()
                
                cursor.execute("""
                    UPDATE meal_options SET
                        name = %s, normalized_name = %s, description = %s,
                        price_vnd = %s, category = %s, is_vegetarian = %s,
                        is_vegan = %s, is_halal = %s, is_gluten_free = %s,
                        calories = %s, prep_time_minutes = %s, image_name = %s,
                        is_available = %s, spicy_level = %s, updated_at = NOW()
                    WHERE id = %s
                """, (
                    data['name'], normalize_text(data['name']), data.get('description'),
                    data.get('priceVnd'), data.get('category'), data.get('isVegetarian'),
                    data.get('isVegan'), data.get('isHalal'), data.get('isGlutenFree'),
                    data.get('calories'), data.get('prepTimeMinutes'), data.get('imageName'),
                    data.get('isAvailable'), data.get('spicyLevel'), meal_option.id
                ))
                
                conn.commit()
                return True
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                conn.rollback()
                return False
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            if meal_option.id in self._in_memory_store:
                self._in_memory_store[meal_option.id] = meal_option
                return True
            return False
    
    def delete_meal_option(self, meal_option_id: int) -> bool:
        """Xóa meal option"""
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM meal_options WHERE id = %s", (meal_option_id,))
                conn.commit()
                return cursor.rowcount > 0
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return False
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            if meal_option_id in self._in_memory_store:
                del self._in_memory_store[meal_option_id]
                return True
            return False
    
    def _row_to_meal_option(self, row: Dict[str, Any]) -> MealOption:
        """Convert MySQL row sang MealOption object"""
        return MealOption(
            id=row['id'],
            diningPlaceId=row.get('dining_place_id'),
            name=row['name'],
            description=row.get('description'),
            priceVnd=row.get('price_vnd'),
            category=row.get('category'),
            isVegetarian=bool(row.get('is_vegetarian', False)),
            isVegan=bool(row.get('is_vegan', False)),
            isHalal=bool(row.get('is_halal', False)),
            isGlutenFree=bool(row.get('is_gluten_free', False)),
            calories=row.get('calories'),
            prepTimeMinutes=row.get('prep_time_minutes'),
            imageName=row.get('image_name'),
            isAvailable=bool(row.get('is_available', True)),
            spicyLevel=row.get('spicy_level', 0)
        )
