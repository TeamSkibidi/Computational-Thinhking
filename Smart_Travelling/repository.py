import os
import logging
from typing import List, Optional
from do_an.models import Place, Address
from do_an.BE.app.utils.normalize_text import normalize_text

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Try to import MySQL connector
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
    logger.info("MySQL connector imported successfully")
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("MySQL connector not available, using in-memory storage")


def _conn():
    """Create database connection with proper configuration"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "travel"),
            autocommit=False,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        logger.debug(f"Connected to database: {os.getenv('DB_NAME', 'travel')}")
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise


class PlaceRepository:
    def __init__(self):
        """Initialize repository with MySQL or fallback to in-memory"""
        self.use_mysql = MYSQL_AVAILABLE and os.getenv("DB_HOST") is not None
        if not self.use_mysql:
            logger.info("Using in-memory storage")
            self._places: List[Place] = []
    
    def find_by_keyword(self, keyword: str) -> List[Place]:
        """Find places by keyword"""
        logger.debug(f"Searching for keyword: {keyword}")
        
        if self.use_mysql:
            return self._find_by_keyword_mysql(keyword)
        else:
            return self._find_by_keyword_memory(keyword)
    
    def _find_by_keyword_mysql(self, keyword: str) -> List[Place]:
        """Find places using MySQL"""
        kw = f"%{keyword}%"
        sql = """
        SELECT p.*, a.id as a_id, a.house_number, a.street, a.ward, a.district, a.city, a.lat, a.lng, a.url
        FROM places p LEFT JOIN addresses a ON p.address_id=a.id
        WHERE p.normalized_name LIKE %s
        ORDER BY p.popularity DESC, p.rating DESC;
        """
        
        try:
            with _conn() as c:
                cur = c.cursor(dictionary=True)
                cur.execute(sql, (kw,))
                rows = cur.fetchall()
                logger.debug(f"Found {len(rows)} results in MySQL")
            
            out = []
            for r in rows:
                addr = Address(
                    houseNumber=r.get("house_number"), 
                    street=r.get("street"),
                    ward=r.get("ward"), 
                    district=r.get("district"),
                    city=r.get("city"), 
                    lat=r.get("lat"), 
                    lng=r.get("lng"),
                    url=r.get("url")
                )
                out.append(Place(
                    id=r["id"], 
                    name=r["name"], 
                    priceVnd=r.get("price_vnd"),
                    summary=r.get("summary"), 
                    description=r.get("description"),
                    openTime=r.get("open_time"), 
                    closeTime=r.get("close_time"),
                    phone=r.get("phone"), 
                    rating=float(r["rating"]) if r.get("rating") is not None else None,
                    reviewCount=r.get("review_count"), 
                    popularity=r.get("popularity"),
                    imageName=r.get("image_name"), 
                    address=addr
                ))
            return out
        except Error as e:
            logger.error(f"MySQL query error: {e}")
            return []
    
    def _find_by_keyword_memory(self, keyword: str) -> List[Place]:
        """Find places using in-memory storage"""
        normalized_keyword = normalize_text(keyword).lower()
        
        results = []
        for place in self._places:
            if normalized_keyword in normalize_text(place.name).lower():
                results.append(place)
            elif place.summary and normalized_keyword in normalize_text(place.summary).lower():
                results.append(place)
            elif place.description and normalized_keyword in normalize_text(place.description).lower():
                results.append(place)
            elif place.address and place.address.city and normalized_keyword in normalize_text(place.address.city).lower():
                results.append(place)
        
        logger.debug(f"Found {len(results)} results in memory")
        return results
    
    def save_place(self, place: Place) -> int:
        """Save a new place"""
        logger.debug(f"Saving place: {place.name}")
        
        if self.use_mysql:
            return self._save_place_mysql(place)
        else:
            return self._save_place_memory(place)
    
    def _save_place_mysql(self, place: Place) -> int:
        """Save place to MySQL using place.to_json()"""
        norm = normalize_text(place.name)
        
        try:
            with _conn() as c:
                cur = c.cursor()
                
                # Save address first
                addr_id = None
                if place.address:
                    addr_data = place.address.model_dump()
                    cur.execute("""
                        INSERT INTO addresses (house_number, street, ward, district, city, lat, lng, url)
                        VALUES (%(houseNumber)s, %(street)s, %(ward)s, %(district)s, %(city)s, %(lat)s, %(lng)s, %(url)s)
                    """, addr_data)
                    addr_id = cur.lastrowid
                    logger.debug(f"Saved address with ID: {addr_id}")
                
                # Save place - exclude address from dict (already saved above)
                cur.execute("""
                    INSERT INTO places 
                    (name, normalized_name, price_vnd, summary, description, open_time, close_time, phone, rating, review_count, popularity, image_name, address_id)
                    VALUES (%(name)s, %(normalized_name)s, %(priceVnd)s, %(summary)s, %(description)s, %(openTime)s, %(closeTime)s, %(phone)s, %(rating)s, %(reviewCount)s, %(popularity)s, %(imageName)s, %(address_id)s)
                """, {
                    'name': place.name,
                    'normalized_name': norm,
                    'priceVnd': place.priceVnd,
                    'summary': place.summary,
                    'description': place.description,
                    'openTime': place.openTime,
                    'closeTime': place.closeTime,
                    'phone': place.phone,
                    'rating': place.rating,
                    'reviewCount': place.reviewCount,
                    'popularity': place.popularity,
                    'imageName': place.imageName,
                    'address_id': addr_id
                })
                
                place_id = cur.lastrowid
                c.commit()
                logger.info(f"Saved place with ID: {place_id}")
                return place_id
                
        except Error as e:
            logger.error(f"Error saving place: {e}")
            raise
    
    def _save_place_memory(self, place: Place) -> int:
        """Save place to memory"""
        if place.id is None:
            place.id = self._get_next_id()
        
        existing_index = self._find_index_by_id(place.id)
        if existing_index is not None:
            self._places[existing_index] = place
            logger.debug(f"Updated place with ID: {place.id}")
        else:
            self._places.append(place)
            logger.debug(f"Added new place with ID: {place.id}")
        
        return place.id
    
    def update_place(self, place: Place) -> bool:
        """Update existing place"""
        if not place.id:
            logger.warning("Cannot update place without ID")
            return False
        
        logger.debug(f"Updating place ID: {place.id}")
        
        if self.use_mysql:
            return self._update_place_mysql(place)
        else:
            return self._update_place_memory(place)
    
    def _update_place_mysql(self, place: Place) -> bool:
        """Update place in MySQL"""
        try:
            with _conn() as c:
                cur = c.cursor()
                cur.execute("""
                    UPDATE places 
                    SET price_vnd=%(priceVnd)s, summary=%(summary)s, description=%(description)s, 
                        open_time=%(openTime)s, close_time=%(closeTime)s, phone=%(phone)s, 
                        rating=%(rating)s, review_count=%(reviewCount)s, 
                        popularity=%(popularity)s, image_name=%(imageName)s
                    WHERE id=%(id)s
                """, {
                    'priceVnd': place.priceVnd,
                    'summary': place.summary,
                    'description': place.description,
                    'openTime': place.openTime,
                    'closeTime': place.closeTime,
                    'phone': place.phone,
                    'rating': place.rating,
                    'reviewCount': place.reviewCount,
                    'popularity': place.popularity,
                    'imageName': place.imageName,
                    'id': place.id
                })
                c.commit()
                success = cur.rowcount > 0
                logger.info(f"Updated place ID {place.id}: {success}")
                return success
        except Error as e:
            logger.error(f"Error updating place: {e}")
            return False
    
    def _update_place_memory(self, place: Place) -> bool:
        """Update place in memory"""
        index = self._find_index_by_id(place.id)
        if index is not None:
            self._places[index] = place
            return True
        return False
    
    def get_place_by_id(self, id_: int) -> Optional[Place]:
        """Get place by ID"""
        logger.debug(f"Getting place by ID: {id_}")
        
        if self.use_mysql:
            return self._get_place_by_id_mysql(id_)
        else:
            return self._get_place_by_id_memory(id_)
    
    def _get_place_by_id_mysql(self, id_: int) -> Optional[Place]:
        """Get place from MySQL"""
        sql = """
        SELECT p.*, a.house_number, a.street, a.ward, a.district, a.city, a.lat, a.lng, a.url
        FROM places p LEFT JOIN addresses a ON p.address_id=a.id
        WHERE p.id=%s
        """
        
        try:
            with _conn() as c:
                cur = c.cursor(dictionary=True)
                cur.execute(sql, (id_,))
                r = cur.fetchone()
            
            if not r:
                logger.debug(f"Place ID {id_} not found")
                return None
            
            addr = Address(
                houseNumber=r.get("house_number"), 
                street=r.get("street"),
                ward=r.get("ward"), 
                district=r.get("district"),
                city=r.get("city"), 
                lat=r.get("lat"), 
                lng=r.get("lng"),
                url=r.get("url")
            )
            
            place = Place(
                id=r["id"], 
                name=r["name"], 
                priceVnd=r.get("price_vnd"),
                summary=r.get("summary"), 
                description=r.get("description"),
                openTime=r.get("open_time"), 
                closeTime=r.get("close_time"), 
                phone=r.get("phone"),
                rating=float(r["rating"]) if r.get("rating") is not None else None,
                reviewCount=r.get("review_count"), 
                popularity=r.get("popularity"),
                imageName=r.get("image_name"), 
                address=addr
            )
            logger.debug(f"Found place: {place.name}")
            return place
            
        except Error as e:
            logger.error(f"Error getting place by ID: {e}")
            return None
    
    def _get_place_by_id_memory(self, id_: int) -> Optional[Place]:
        """Get place from memory"""
        for place in self._places:
            if place.id == id_:
                return place
        return None
    
    def delete_by_id(self, place_id: int) -> bool:
        """Delete place by ID"""
        logger.debug(f"Deleting place ID: {place_id}")
        
        if self.use_mysql:
            return self._delete_by_id_mysql(place_id)
        else:
            return self._delete_by_id_memory(place_id)
    
    def _delete_by_id_mysql(self, place_id: int) -> bool:
        """Delete from MySQL"""
        try:
            with _conn() as c:
                cur = c.cursor()
                cur.execute("DELETE FROM places WHERE id=%s", (place_id,))
                c.commit()
                success = cur.rowcount > 0
                logger.info(f"Deleted place ID {place_id}: {success}")
                return success
        except Error as e:
            logger.error(f"Error deleting place: {e}")
            return False
    
    def _delete_by_id_memory(self, place_id: int) -> bool:
        """Delete from memory"""
        index = self._find_index_by_id(place_id)
        if index is not None:
            del self._places[index]
            return True
        return False
    
    def get_all(self) -> List[Place]:
        """Get all places"""
        if self.use_mysql:
            return self.find_by_keyword("")
        else:
            return self._places.copy()
    
    def count(self) -> int:
        """Count total places"""
        if self.use_mysql:
            try:
                with _conn() as c:
                    cur = c.cursor()
                    cur.execute("SELECT COUNT(*) FROM places")
                    return cur.fetchone()[0]
            except Error as e:
                logger.error(f"Error counting places: {e}")
                return 0
        else:
            return len(self._places)
    
    # Helper methods for in-memory storage
    def _get_next_id(self) -> int:
        if not self._places:
            return 1
        return max(p.id for p in self._places if p.id is not None) + 1
    
    def _find_index_by_id(self, place_id: int) -> Optional[int]:
        for i, place in enumerate(self._places):
            if place.id == place_id:
                return i
        return None

