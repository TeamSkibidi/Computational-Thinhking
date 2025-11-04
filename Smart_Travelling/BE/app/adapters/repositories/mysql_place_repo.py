"""MySQL implementation của IPlaceRepository"""
import logging
import aiomysql
from typing import List, Optional
from app.application.interfaces.place_repository import IPlaceRepository
from app.domain.entities.PlaceLite import PlaceLite
from app.domain.entities.Address import Address
from app.infrastructure.database.connection import get_connection
from app.utils.normalize_text import normalize_text


logger = logging.getLogger(__name__) # Thiết lập logger cho module này


class MySQLPlaceRepository(IPlaceRepository):
    """
    MySQL implementation of place repository
    Structure:
        1. __init__: Khởi tạo (nếu cần)
        2. PUBLIC METHODS: Implement interface (không có prefix _)
        3. PRIVATE METHODS: Helper methods (có prefix _)
        4. STATIC METHODS: Utility methods
    """
    
    def __init__(self):
        """Khởi tạo nếu cần connection pool hoặc config"""
        self.logger = logging.getLogger(self.__class__.__name__)

    async def find_by_keyword(self, keyword: str) -> List[PlaceLite]:
        """ Gọi private method _find_by_keyword_mysql để xử lý logic """
        return await self._find_by_keyword_mysql(keyword)
    
    async def save(self, place: PlaceLite) -> int:
        """Cài đặt hàm lưu place vào MySQL"""
        return await self._save_place_mysql(place)
    
    async def update(self, place: PlaceLite) -> bool:
        """Cài đặt hàm cập nhật place vào MySQL"""
        return await self._update_place_mysql(place)
    
    async def get_by_id(self, place_id: int) -> Optional[PlaceLite]:
        """Cài đặt hàm lấy place theo ID từ MySQL"""
        return await self._get_place_by_id_mysql(place_id)
    
    async def delete_by_id(self, place_id: int) -> bool:
        """Cài đặt hàm xóa place theo ID từ MySQL"""
        return await self._delete_by_id_mysql(place_id)
    
    async def get_all(self) -> List[PlaceLite]:
        """Cài đặt hàm lấy tất cả places từ MySQL"""
        return await self.find_by_keyword("")
    
    async def count(self) -> int:
        """Cài đặt hàm đếm số lượng places từ MySQL"""
        return await self._count_places_mysql()
    
    async def find_by_city(self, city: str) -> List[PlaceLite]:
        """Cài đặt hàm tìm kiếm theo thành phố từ MySQL"""
        return await self._find_by_city_mysql(city)
    
    
    async def _find_by_keyword_mysql(self, keyword: str) -> List[PlaceLite]:
        """tìm kiếm trong MySQL với độ chính xác cao theo tên hoặc thành phố"""
        
        norm_kw = normalize_text(keyword) #chuyển về chuẩn hóa
        norm_kw_like = f"%{norm_kw}%" 
        norm_kw_start = f"{norm_kw}%"
        
        async with get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Tìm theo TÊN địa điểm 
                await cur.execute("""
                    SELECT p.*, a.house_number, a.street, a.ward, a.district, a.city, a.lat, a.lng, a.url,
                           CASE
                               WHEN p.normalized_name = %s THEN 1
                               WHEN p.normalized_name LIKE %s THEN 2
                               WHEN p.normalized_name LIKE %s THEN 3
                               ELSE 4
                            END as relevance_score
                    FROM places p
                    LEFT JOIN addresses a ON p.address_id = a.id
                    WHERE p.normalized_name LIKE %s
                    ORDER BY relevance_score ASC, 
                             p.popularity DESC, 
                             p.rating DESC
                """, (norm_kw, norm_kw_start, norm_kw_like, norm_kw_like))
                rows = await cur.fetchall()
                
                # Nếu không có kết quả tên thì tìm theo THÀNH PHỐ
                if not rows:
                    self.logger.debug(f"No place name matches, searching by city: {keyword}")
                    await cur.execute("""
                        SELECT p.*,a.house_number, a.street, a.ward, a.district, a.city, a.lat, a.lng, a.url,
                               5 as relevance_score
                        FROM places p
                        LEFT JOIN addresses a ON p.address_id = a.id
                        WHERE a.city LIKE %s
                        ORDER BY p.popularity DESC, 
                                 p.rating DESC
                    """, (norm_kw_like,))
                    rows = await cur.fetchall()
        
        self.logger.debug(f"Found {len(rows)} places for keyword: {keyword}")
        return [self._row_to_entity(r) for r in rows]
    
    async def _save_place_mysql(self, place: PlaceLite) -> int:
        """ Kiểm tra trùng theo tên hoặc tọa độ """
        async with get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                norm_name = normalize_text(place.name)
                lat = place.address.lat if place.address else None
                lng = place.address.lng if place.address else None
                
                if lat and lng:
                    # Kiểm tra theo tên và tọa độ (tolerance ±0.0001 độ ~ 10m)
                    await cur.execute("""
                        SELECT p.id, p.name
                        FROM places p
                        LEFT JOIN addresses a ON p.address_id = a.id
                        WHERE p.normalized_name = %s
                          AND ABS(a.lat - %s) < 0.0001
                          AND ABS(a.lng - %s) < 0.0001
                        LIMIT 1
                    """, (norm_name, lat, lng))
                    existing = await cur.fetchone()
                    
                    if existing:
                        # Đã tồn tại trả về ID hiện có báo 
                        self.logger.info(f"Dữ liệu của địa điểm '{place.name}' đã tồn tại (ID: {existing['id']}) bỏ qua ")
                        return existing['id']
                
                # Lưu địa chỉ trước (nếu không trùng)
                addr_id = await self._save_address_mysql(cur, place.address)
                
                # Lưu thông tin địa điểm
                await cur.execute("""
                    INSERT INTO places 
                    (name, normalized_name, price_vnd, summary, description, 
                     open_time, close_time, phone, rating, review_count, 
                     popularity, image_name, address_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    place.name,
                    normalize_text(place.name),
                    place.priceVnd,
                    place.summary,
                    place.description,
                    place.openTime,
                    place.closeTime,
                    place.phone,
                    place.rating,
                    place.reviewCount,
                    place.popularity,
                    place.imageName,
                    addr_id
                ))
                
                place_id = cur.lastrowid
                self.logger.info(f"Lưu địa điểm '{place.name}' với id là: {place_id}")
                return place_id
    
    async def _save_address_mysql(self, cursor, address: Optional[Address]) -> Optional[int]:
        """ Lưu address vào MySQL """
        if not address:
            return None
        
        await cursor.execute("""
            INSERT INTO addresses 
            (house_number, street, ward, district, city, lat, lng, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            address.houseNumber,
            address.street,
            address.ward,
            address.district,
            address.city,
            address.lat,
            address.lng,
            address.url
        ))
        return cursor.lastrowid
    
    async def _update_place_mysql(self, place: PlaceLite) -> bool:
        """cập nhật place trong MySQL"""
        if not place.id:
            self.logger.warning("không thể cập nhật place khi không có ID")
            return False
        
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE places 
                    SET price_vnd=%s, summary=%s, description=%s, 
                        open_time=%s, close_time=%s, phone=%s, 
                        rating=%s, review_count=%s, popularity=%s, 
                        image_name=%s
                    WHERE id=%s
                """, (
                    place.priceVnd, place.summary, place.description,
                    place.openTime, place.closeTime, place.phone,
                    place.rating, place.reviewCount, place.popularity,
                    place.imageName, place.id
                ))
                success = cur.rowcount > 0
                
        self.logger.info(f"Cập nhật {place.id}: {success}")
        return success
    
    async def _get_place_by_id_mysql(self, place_id: int) -> Optional[PlaceLite]:
        """lấy place từ MySQL theo ID"""
        async with get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT p.*, 
                           a.house_number, a.street, a.ward, 
                           a.district, a.city, a.lat, a.lng, a.url
                    FROM places p
                    LEFT JOIN addresses a ON p.address_id = a.id
                    WHERE p.id = %s
                """, (place_id,))
                row = await cur.fetchone()
        
        if not row:
            self.logger.debug(f"id địa điểm {place_id} không tìm thấy")
            return None
        
        return self._row_to_entity(row)
    
    async def _delete_by_id_mysql(self, place_id: int) -> bool:
        """Xóa place khỏi MySQL"""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM places WHERE id=%s", (place_id,))
                success = cur.rowcount > 0
        
        self.logger.info(f"Xóa id địa điểm {place_id}: {success}")
        return success
    
    async def _count_places_mysql(self) -> int:
        """Đếm số lượng place trong MySQL"""
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM places")
                result = await cur.fetchone()
                return result[0] if result else 0
    
    async def _find_by_city_mysql(self, city: str) -> List[PlaceLite]:
        """Tìm place theo thành phố trong MySQL"""
        norm_city = normalize_text(city)
        
        async with get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT p.*, 
                           a.house_number, a.street, a.ward, 
                           a.district, a.city, a.lat, a.lng, a.url
                    FROM places p
                    JOIN addresses a ON p.address_id = a.id
                    WHERE a.city LIKE %s
                    ORDER BY p.popularity DESC
                """, (f"%{norm_city}%",))
                rows = await cur.fetchall()
        
        return [self._row_to_entity(r) for r in rows]

    
    @staticmethod
    def _row_to_entity(row: dict) -> PlaceLite:
        """ Chuyển đổi hàng dữ liệu từ database thành PlaceLite entity """
        address = Address(
            house_number=row.get("house_number"),
            street=row.get("street"),
            ward=row.get("ward"),
            district=row.get("district"),
            city=row.get("city"),
            lat=row.get("lat"),
            lng=row.get("lng"),
            url=row.get("url")
        )
        
        return PlaceLite(
            id=row["id"],
            name=row["name"],
            price_vnd=row.get("price_vnd"),
            summary=row.get("summary"),
            description=row.get("description"),
            open_time=row.get("open_time"),
            close_time=row.get("close_time"),
            phone=row.get("phone"),
            rating=row.get("rating"),
            review_count=row.get("review_count", 0),
            popularity=row.get("popularity", 0),
            image_name=row.get("image_name"),
            address=address
        )
    
    @staticmethod
    def _entity_to_dict(place: PlaceLite) -> dict:
        """Chuyển dữ liệu từ Place entity sang dict"""
        return {
            "id": place.id,
            "name": place.name,
            "price_vnd": place.priceVnd,
            "rating": place.rating,
            # ... các field khác
        }