#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MealSlotRepository: Quản lý các slot bữa ăn trong meal plan
Chức năng:
- CRUD operations cho meal slots (breakfast, lunch, dinner, snack)
- Link MealPlan với MealOption
- Tính tổng calories và nutrition cho từng slot
- Quản lý thời gian và portion size
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import time
import mysql.connector
from mysql.connector import Error

from entities.meal_slot_model import MealSlot

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


class MealSlotRepository:
    """Repository quản lý MealSlot với hybrid storage"""
    
    def __init__(self):
        self.use_mysql = _conn() is not None
        self._in_memory_store: Dict[int, MealSlot] = {}
        self._next_id = 1
        logger.info(f"MealSlotRepository initialized. Using MySQL: {self.use_mysql}")
    
    def save_meal_slot(self, meal_slot: MealSlot) -> int:
        """
        Lưu meal slot mới
        Args:
            meal_slot: MealSlot object
        Returns:
            meal_slot_id
        """
        logger.debug(f"Saving meal slot: {meal_slot.slotType}")
        
        if self.use_mysql:
            return self._save_to_mysql(meal_slot)
        else:
            return self._save_to_memory(meal_slot)
    
    def _save_to_mysql(self, meal_slot: MealSlot) -> int:
        """Lưu meal slot vào MySQL"""
        conn = _conn()
        if not conn:
            return self._save_to_memory(meal_slot)
        
        try:
            cursor = conn.cursor()
            data = meal_slot.to_json()
            
            cursor.execute("""
                INSERT INTO meal_slots
                (meal_plan_id, meal_option_id, dining_place_id,
                 slot_type, slot_order, scheduled_time,
                 portion_size, serving_unit, actual_calories,
                 actual_protein_g, actual_carbs_g, actual_fat_g,
                 is_completed, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('mealPlanId'),
                data.get('mealOptionId'),
                data.get('diningPlaceId'),
                data['slotType'],
                data.get('slotOrder', 1),
                data.get('scheduledTime'),
                data.get('portionSize', 1.0),
                data.get('servingUnit', 'serving'),
                data.get('actualCalories'),
                data.get('actualProteinG'),
                data.get('actualCarbsG'),
                data.get('actualFatG'),
                data.get('isCompleted', False),
                data.get('notes')
            ))
            
            meal_slot_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved meal slot to MySQL with ID: {meal_slot_id}")
            return meal_slot_id
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            conn.rollback()
            return self._save_to_memory(meal_slot)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def _save_to_memory(self, meal_slot: MealSlot) -> int:
        """Lưu vào memory"""
        meal_slot_id = self._next_id
        self._next_id += 1
        self._in_memory_store[meal_slot_id] = meal_slot
        logger.info(f"Saved meal slot to memory with ID: {meal_slot_id}")
        return meal_slot_id
    
    def get_meal_slot_by_id(self, meal_slot_id: int) -> Optional[MealSlot]:
        """Lấy meal slot theo ID"""
        if self.use_mysql:
            return self._get_from_mysql(meal_slot_id)
        else:
            return self._in_memory_store.get(meal_slot_id)
    
    def _get_from_mysql(self, meal_slot_id: int) -> Optional[MealSlot]:
        """Lấy từ MySQL"""
        conn = _conn()
        if not conn:
            return self._in_memory_store.get(meal_slot_id)
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM meal_slots WHERE id = %s", (meal_slot_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_meal_slot(row)
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            return self._in_memory_store.get(meal_slot_id)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def find_by_meal_plan(self, meal_plan_id: int) -> List[MealSlot]:
        """
        Lấy tất cả meal slots của một meal plan
        Sắp xếp theo slot_order và scheduled_time
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_slots
                    WHERE meal_plan_id = %s
                    ORDER BY slot_order ASC, scheduled_time ASC
                """, (meal_plan_id,))
                
                return [self._row_to_meal_slot(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [ms for ms in self._in_memory_store.values() 
                      if ms.mealPlanId == meal_plan_id]
            results.sort(key=lambda x: (x.slotOrder or 1, x.scheduledTime or time(0, 0)))
            return results
    
    def find_by_slot_type(self, meal_plan_id: int, slot_type: str) -> List[MealSlot]:
        """
        Lấy meal slots theo type (breakfast, lunch, dinner, snack)
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_slots
                    WHERE meal_plan_id = %s AND slot_type = %s
                    ORDER BY scheduled_time ASC
                """, (meal_plan_id, slot_type))
                
                return [self._row_to_meal_slot(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [ms for ms in self._in_memory_store.values()
                      if ms.mealPlanId == meal_plan_id and ms.slotType == slot_type]
            results.sort(key=lambda x: x.scheduledTime or time(0, 0))
            return results
    
    def find_by_dining_place(self, dining_place_id: int, limit: int = 50) -> List[MealSlot]:
        """
        Lấy meal slots đã đặt tại một dining place
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_slots
                    WHERE dining_place_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (dining_place_id, limit))
                
                return [self._row_to_meal_slot(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [ms for ms in self._in_memory_store.values()
                      if ms.diningPlaceId == dining_place_id]
            return results[:limit]
    
    def get_completed_slots(self, meal_plan_id: int) -> List[MealSlot]:
        """Lấy các slots đã hoàn thành"""
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_slots
                    WHERE meal_plan_id = %s AND is_completed = TRUE
                    ORDER BY slot_order ASC
                """, (meal_plan_id,))
                
                return [self._row_to_meal_slot(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [ms for ms in self._in_memory_store.values()
                      if ms.mealPlanId == meal_plan_id and ms.isCompleted]
            results.sort(key=lambda x: x.slotOrder or 1)
            return results
    
    def get_total_nutrition(self, meal_plan_id: int) -> Dict[str, float]:
        """
        Tính tổng nutrition cho toàn bộ meal plan
        Returns: Dict với calories, protein, carbs, fat
        """
        slots = self.find_by_meal_plan(meal_plan_id)
        
        total = {
            'calories': 0.0,
            'protein_g': 0.0,
            'carbs_g': 0.0,
            'fat_g': 0.0
        }
        
        for slot in slots:
            if slot.actualCalories:
                total['calories'] += slot.actualCalories * slot.portionSize
            if slot.actualProteinG:
                total['protein_g'] += slot.actualProteinG * slot.portionSize
            if slot.actualCarbsG:
                total['carbs_g'] += slot.actualCarbsG * slot.portionSize
            if slot.actualFatG:
                total['fat_g'] += slot.actualFatG * slot.portionSize
        
        return total
    
    def mark_as_completed(self, meal_slot_id: int) -> bool:
        """Đánh dấu meal slot là đã hoàn thành"""
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE meal_slots SET 
                        is_completed = TRUE,
                        completed_at = NOW()
                    WHERE id = %s
                """, (meal_slot_id,))
                
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
            if meal_slot_id in self._in_memory_store:
                self._in_memory_store[meal_slot_id].isCompleted = True
                return True
            return False
    
    def update_meal_slot(self, meal_slot: MealSlot) -> bool:
        """Cập nhật meal slot"""
        if not meal_slot.id:
            return False
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                data = meal_slot.to_json()
                
                cursor.execute("""
                    UPDATE meal_slots SET
                        meal_option_id = %s, dining_place_id = %s,
                        slot_type = %s, slot_order = %s, scheduled_time = %s,
                        portion_size = %s, serving_unit = %s,
                        actual_calories = %s, actual_protein_g = %s,
                        actual_carbs_g = %s, actual_fat_g = %s,
                        is_completed = %s, notes = %s, updated_at = NOW()
                    WHERE id = %s
                """, (
                    data.get('mealOptionId'), data.get('diningPlaceId'),
                    data['slotType'], data.get('slotOrder'), data.get('scheduledTime'),
                    data.get('portionSize'), data.get('servingUnit'),
                    data.get('actualCalories'), data.get('actualProteinG'),
                    data.get('actualCarbsG'), data.get('actualFatG'),
                    data.get('isCompleted'), data.get('notes'), meal_slot.id
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
            if meal_slot.id in self._in_memory_store:
                self._in_memory_store[meal_slot.id] = meal_slot
                return True
            return False
    
    def delete_meal_slot(self, meal_slot_id: int) -> bool:
        """Xóa meal slot"""
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM meal_slots WHERE id = %s", (meal_slot_id,))
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
            if meal_slot_id in self._in_memory_store:
                del self._in_memory_store[meal_slot_id]
                return True
            return False
    
    def _row_to_meal_slot(self, row: Dict[str, Any]) -> MealSlot:
        """Convert MySQL row sang MealSlot object"""
        return MealSlot(
            id=row['id'],
            mealPlanId=row.get('meal_plan_id'),
            mealOptionId=row.get('meal_option_id'),
            diningPlaceId=row.get('dining_place_id'),
            slotType=row['slot_type'],
            slotOrder=row.get('slot_order', 1),
            scheduledTime=row.get('scheduled_time'),
            portionSize=float(row.get('portion_size', 1.0)),
            servingUnit=row.get('serving_unit', 'serving'),
            actualCalories=row.get('actual_calories'),
            actualProteinG=row.get('actual_protein_g'),
            actualCarbsG=row.get('actual_carbs_g'),
            actualFatG=row.get('actual_fat_g'),
            isCompleted=bool(row.get('is_completed', False)),
            notes=row.get('notes')
        )
