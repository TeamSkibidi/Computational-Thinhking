#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MealPlanRepository: Quản lý kế hoạch ăn uống (meal plans)
Chức năng:
- CRUD operations cho meal plans (kế hoạch ăn theo ngày/tuần)
- Tìm kiếm theo user, ngày, mục tiêu (weight loss, muscle gain, etc.)
- Tính tổng calories, nutrition facts
- Link với MealSlot
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import mysql.connector
from mysql.connector import Error

from entities.meal_plan_model import MealPlan

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


class MealPlanRepository:
    """Repository quản lý MealPlan với hybrid storage"""
    
    def __init__(self):
        self.use_mysql = _conn() is not None
        self._in_memory_store: Dict[int, MealPlan] = {}
        self._next_id = 1
        logger.info(f"MealPlanRepository initialized. Using MySQL: {self.use_mysql}")
    
    def save_meal_plan(self, meal_plan: MealPlan) -> int:
        """
        Lưu meal plan mới
        Args:
            meal_plan: MealPlan object
        Returns:
            meal_plan_id
        """
        logger.debug(f"Saving meal plan for date: {meal_plan.planDate}")
        
        if self.use_mysql:
            return self._save_to_mysql(meal_plan)
        else:
            return self._save_to_memory(meal_plan)
    
    def _save_to_mysql(self, meal_plan: MealPlan) -> int:
        """Lưu meal plan vào MySQL"""
        conn = _conn()
        if not conn:
            return self._save_to_memory(meal_plan)
        
        try:
            cursor = conn.cursor()
            data = meal_plan.to_json()
            
            cursor.execute("""
                INSERT INTO meal_plans
                (user_id, plan_date, plan_name, description,
                 target_calories, target_protein_g, target_carbs_g, target_fat_g,
                 goal_type, is_active, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('userId'),
                data['planDate'],
                data.get('planName'),
                data.get('description'),
                data.get('targetCalories'),
                data.get('targetProteinG'),
                data.get('targetCarbsG'),
                data.get('targetFatG'),
                data.get('goalType'),
                data.get('isActive', True),
                data.get('notes')
            ))
            
            meal_plan_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved meal plan to MySQL with ID: {meal_plan_id}")
            return meal_plan_id
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            conn.rollback()
            return self._save_to_memory(meal_plan)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def _save_to_memory(self, meal_plan: MealPlan) -> int:
        """Lưu vào memory"""
        meal_plan_id = self._next_id
        self._next_id += 1
        self._in_memory_store[meal_plan_id] = meal_plan
        logger.info(f"Saved meal plan to memory with ID: {meal_plan_id}")
        return meal_plan_id
    
    def get_meal_plan_by_id(self, meal_plan_id: int) -> Optional[MealPlan]:
        """Lấy meal plan theo ID"""
        if self.use_mysql:
            return self._get_from_mysql(meal_plan_id)
        else:
            return self._in_memory_store.get(meal_plan_id)
    
    def _get_from_mysql(self, meal_plan_id: int) -> Optional[MealPlan]:
        """Lấy từ MySQL"""
        conn = _conn()
        if not conn:
            return self._in_memory_store.get(meal_plan_id)
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM meal_plans WHERE id = %s", (meal_plan_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_meal_plan(row)
            
        except Error as e:
            logger.error(f"MySQL error: {e}")
            return self._in_memory_store.get(meal_plan_id)
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def find_by_user_and_date(self, user_id: int, plan_date: date) -> Optional[MealPlan]:
        """
        Lấy meal plan của user cho một ngày cụ thể
        Args:
            user_id: ID của user
            plan_date: Ngày của meal plan
        Returns:
            MealPlan object hoặc None
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return None
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_plans
                    WHERE user_id = %s AND plan_date = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id, plan_date))
                
                row = cursor.fetchone()
                return self._row_to_meal_plan(row) if row else None
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return None
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            for mp in self._in_memory_store.values():
                if mp.userId == user_id and mp.planDate == plan_date:
                    return mp
            return None
    
    def find_by_user(self, user_id: int, limit: int = 30) -> List[MealPlan]:
        """
        Lấy tất cả meal plans của user (sắp xếp theo ngày mới nhất)
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_plans
                    WHERE user_id = %s
                    ORDER BY plan_date DESC
                    LIMIT %s
                """, (user_id, limit))
                
                return [self._row_to_meal_plan(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [mp for mp in self._in_memory_store.values() if mp.userId == user_id]
            results.sort(key=lambda x: x.planDate, reverse=True)
            return results[:limit]
    
    def find_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[MealPlan]:
        """
        Lấy meal plans của user trong khoảng thời gian
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_plans
                    WHERE user_id = %s 
                      AND plan_date BETWEEN %s AND %s
                    ORDER BY plan_date ASC
                """, (user_id, start_date, end_date))
                
                return [self._row_to_meal_plan(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = []
            for mp in self._in_memory_store.values():
                if mp.userId == user_id and start_date <= mp.planDate <= end_date:
                    results.append(mp)
            results.sort(key=lambda x: x.planDate)
            return results
    
    def find_by_goal_type(self, user_id: int, goal_type: str, limit: int = 30) -> List[MealPlan]:
        """
        Tìm meal plans theo goal type (weight_loss, muscle_gain, maintenance, etc.)
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return []
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_plans
                    WHERE user_id = %s AND goal_type = %s
                    ORDER BY plan_date DESC
                    LIMIT %s
                """, (user_id, goal_type, limit))
                
                return [self._row_to_meal_plan(row) for row in cursor.fetchall()]
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return []
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            results = [mp for mp in self._in_memory_store.values()
                      if mp.userId == user_id and mp.goalType == goal_type]
            results.sort(key=lambda x: x.planDate, reverse=True)
            return results[:limit]
    
    def get_active_plan(self, user_id: int) -> Optional[MealPlan]:
        """
        Lấy meal plan đang active của user
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return None
            
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT * FROM meal_plans
                    WHERE user_id = %s AND is_active = TRUE
                    ORDER BY plan_date DESC
                    LIMIT 1
                """, (user_id,))
                
                row = cursor.fetchone()
                return self._row_to_meal_plan(row) if row else None
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return None
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            for mp in self._in_memory_store.values():
                if mp.userId == user_id and mp.isActive:
                    return mp
            return None
    
    def update_meal_plan(self, meal_plan: MealPlan) -> bool:
        """Cập nhật meal plan"""
        if not meal_plan.id:
            return False
        
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                data = meal_plan.to_json()
                
                cursor.execute("""
                    UPDATE meal_plans SET
                        plan_date = %s, plan_name = %s, description = %s,
                        target_calories = %s, target_protein_g = %s,
                        target_carbs_g = %s, target_fat_g = %s,
                        goal_type = %s, is_active = %s, notes = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    data['planDate'], data.get('planName'), data.get('description'),
                    data.get('targetCalories'), data.get('targetProteinG'),
                    data.get('targetCarbsG'), data.get('targetFatG'),
                    data.get('goalType'), data.get('isActive'), data.get('notes'),
                    meal_plan.id
                ))
                
                conn.commit()
                logger.info(f"Updated meal plan ID: {meal_plan.id}")
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
            if meal_plan.id in self._in_memory_store:
                self._in_memory_store[meal_plan.id] = meal_plan
                return True
            return False
    
    def deactivate_other_plans(self, user_id: int, active_plan_id: int) -> bool:
        """
        Deactivate tất cả plans khác của user (chỉ giữ 1 plan active)
        """
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE meal_plans SET is_active = FALSE
                    WHERE user_id = %s AND id != %s
                """, (user_id, active_plan_id))
                
                conn.commit()
                return True
                
            except Error as e:
                logger.error(f"MySQL error: {e}")
                return False
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            for mp in self._in_memory_store.values():
                if mp.userId == user_id and mp.id != active_plan_id:
                    mp.isActive = False
            return True
    
    def delete_meal_plan(self, meal_plan_id: int) -> bool:
        """Xóa meal plan"""
        if self.use_mysql:
            conn = _conn()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM meal_plans WHERE id = %s", (meal_plan_id,))
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
            if meal_plan_id in self._in_memory_store:
                del self._in_memory_store[meal_plan_id]
                return True
            return False
    
    def _row_to_meal_plan(self, row: Dict[str, Any]) -> MealPlan:
        """Convert MySQL row sang MealPlan object"""
        return MealPlan(
            id=row['id'],
            userId=row.get('user_id'),
            planDate=row['plan_date'],
            planName=row.get('plan_name'),
            description=row.get('description'),
            targetCalories=row.get('target_calories'),
            targetProteinG=row.get('target_protein_g'),
            targetCarbsG=row.get('target_carbs_g'),
            targetFatG=row.get('target_fat_g'),
            goalType=row.get('goal_type'),
            isActive=bool(row.get('is_active', True)),
            notes=row.get('notes')
        )
