#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Transformer - Chuyển đổi dữ liệu giữa API response và Database models
"""

import logging
from typing import Dict, Any, Optional, List
from entities.dining_place_model import DiningPlace
from models import Address

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiningPlaceTransformer:
    """
    Transformer để chuyển đổi data giữa:
    - API Response (SERPAPI/Google) → DiningPlace Object
    - DiningPlace Object → Database Row
    - Database Row → DiningPlace Object
    """
    
    @staticmethod
    def from_serpapi_to_model(api_data: Dict[str, Any]) -> Optional[DiningPlace]:
        """
        Chuyển đổi SERPAPI response → DiningPlace model
        
        Args:
            api_data: Dict từ SERPAPI local_results
        
        Returns:
            DiningPlace object hoặc None nếu lỗi
        
        Example SERPAPI data structure:
        {
            "title": "Phở 24",
            "address": "5 Nguyễn Thiệp, Quận 1",
            "rating": 4.5,
            "reviews": 1200,
            "type": "Vietnamese restaurant",
            "phone": "+84 28 3822 6278",
            "gps_coordinates": {"latitude": 10.774, "longitude": 106.702},
            "price": "$$",
            "hours": "7:00 AM - 11:00 PM"
        }
        """
        try:
            # Extract basic info
            name = api_data.get('title', 'Unknown')
            
            # Extract address
            address_str = api_data.get('address', '')
            gps = api_data.get('gps_coordinates', {})
            
            address = Address(
                street=address_str,
                lat=gps.get('latitude'),
                lng=gps.get('longitude')
            ) if address_str or gps else None
            
            # Extract rating & reviews
            rating = api_data.get('rating')
            review_count = api_data.get('reviews', 0)
            
            # Determine cuisine type from 'type' field
            place_type = api_data.get('type', '').lower()
            cuisine_type = DiningPlaceTransformer._extract_cuisine_type(place_type)
            
            # Extract price range (convert symbols to VND)
            price_symbol = api_data.get('price', '')
            price_range_vnd = DiningPlaceTransformer._convert_price_symbol_to_vnd(price_symbol)
            
            # Extract phone
            phone = api_data.get('phone')
            
            # Extract hours
            hours = api_data.get('hours', '')
            open_time, close_time = DiningPlaceTransformer._parse_hours(hours)
            
            # Create DiningPlace object
            dining_place = DiningPlace(
                name=name,
                cuisineType=cuisine_type,
                priceRangeVnd=price_range_vnd,
                summary=api_data.get('description', place_type),
                openTime=open_time,
                closeTime=close_time,
                phone=phone,
                rating=rating,
                reviewCount=review_count,
                hasParking=False,  # Not available from API
                hasWifi=False,  # Not available from API
                hasDelivery=False,  # Not available from API
                address=address
            )
            
            logger.info(f"✅ Transformed SERPAPI data: {name}")
            return dining_place
            
        except Exception as e:
            logger.error(f"❌ Error transforming SERPAPI data: {e}")
            logger.error(f"Data: {api_data}")
            return None
    
    @staticmethod
    def from_google_to_model(api_data: Dict[str, Any]) -> Optional[DiningPlace]:
        """
        Chuyển đổi Google Places API response → DiningPlace model
        
        Args:
            api_data: Dict từ Google Places API
        
        Returns:
            DiningPlace object hoặc None
        
        Example Google data structure:
        {
            "name": "Phở 24",
            "vicinity": "5 Nguyễn Thiệp, Quận 1",
            "rating": 4.5,
            "user_ratings_total": 1200,
            "types": ["restaurant", "food"],
            "geometry": {
                "location": {"lat": 10.774, "lng": 106.702}
            },
            "price_level": 2,
            "opening_hours": {
                "open_now": true,
                "weekday_text": ["Monday: 7:00 AM - 11:00 PM", ...]
            }
        }
        """
        try:
            # Extract basic info
            name = api_data.get('name', 'Unknown')
            
            # Extract address
            address_str = api_data.get('vicinity', '') or api_data.get('formatted_address', '')
            geometry = api_data.get('geometry', {})
            location = geometry.get('location', {})
            
            address = Address(
                street=address_str,
                lat=location.get('lat'),
                lng=location.get('lng')
            ) if address_str or location else None
            
            # Extract rating & reviews
            rating = api_data.get('rating')
            review_count = api_data.get('user_ratings_total', 0)
            
            # Determine cuisine type from 'types' field
            types = api_data.get('types', [])
            cuisine_type = DiningPlaceTransformer._extract_cuisine_from_types(types)
            
            # Extract price level (1-4) → VND range
            price_level = api_data.get('price_level')
            price_range_vnd = DiningPlaceTransformer._convert_price_level_to_vnd(price_level)
            
            # Extract phone
            phone = api_data.get('formatted_phone_number')
            
            # Extract opening hours
            opening_hours = api_data.get('opening_hours', {})
            weekday_text = opening_hours.get('weekday_text', [])
            open_time, close_time = DiningPlaceTransformer._parse_google_hours(weekday_text)
            
            # Create DiningPlace object
            dining_place = DiningPlace(
                name=name,
                cuisineType=cuisine_type,
                priceRangeVnd=price_range_vnd,
                summary=f"{cuisine_type} restaurant",
                openTime=open_time,
                closeTime=close_time,
                phone=phone,
                rating=rating,
                reviewCount=review_count,
                hasParking=False,
                hasWifi=False,
                hasDelivery=False,
                address=address
            )
            
            logger.info(f"✅ Transformed Google data: {name}")
            return dining_place
            
        except Exception as e:
            logger.error(f"❌ Error transforming Google data: {e}")
            logger.error(f"Data: {api_data}")
            return None
    
    @staticmethod
    def model_to_db_dict(dining_place: DiningPlace, address_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Chuyển đổi DiningPlace model → Dict để INSERT vào database
        
        Args:
            dining_place: DiningPlace object
            address_id: ID của address đã lưu (nếu có)
        
        Returns:
            Dict với keys match database columns
        """
        from normalize_text import normalize_text
        
        return {
            'name': dining_place.name,
            'normalized_name': normalize_text(dining_place.name),
            'cuisine_type': dining_place.cuisineType,
            'price_range_vnd': dining_place.priceRangeVnd,
            'summary': dining_place.summary,
            'description': dining_place.description,
            'open_time': dining_place.openTime,
            'close_time': dining_place.closeTime,
            'phone': dining_place.phone,
            'rating': dining_place.rating,
            'review_count': dining_place.reviewCount,
            'popularity': dining_place.popularity or 0,
            'image_name': dining_place.imageName,
            'has_parking': dining_place.hasParking,
            'has_wifi': dining_place.hasWifi,
            'has_delivery': dining_place.hasDelivery,
            'address_id': address_id
        }
    
    @staticmethod
    def db_row_to_model(row: tuple) -> DiningPlace:
        """
        Chuyển đổi database row → DiningPlace model
        
        Args:
            row: Tuple từ cursor.fetchone() (33 fields)
                [0-16]: dining_places columns
                [17-32]: addresses columns (LEFT JOIN)
        
        Returns:
            DiningPlace object
        """
        # Parse address (nếu có)
        address = None
        if row[17]:  # address.id exists
            address = Address(
                houseNumber=row[18],
                street=row[19],
                ward=row[20],
                district=row[21],
                city=row[22],
                lat=row[23],
                lng=row[24],
                url=row[25]
            )
        
        # Create DiningPlace
        return DiningPlace(
            id=row[0],
            name=row[1],
            cuisineType=row[3],
            priceRangeVnd=row[4],
            summary=row[5],
            description=row[6],
            openTime=row[7],
            closeTime=row[8],
            phone=row[9],
            rating=row[10],
            reviewCount=row[11],
            popularity=row[12],
            imageName=row[13],
            hasParking=bool(row[14]),
            hasWifi=bool(row[15]),
            hasDelivery=bool(row[16]),
            address=address
        )
    
    # ========================================
    # Helper Methods
    # ========================================
    
    @staticmethod
    def _extract_cuisine_type(place_type_str: str) -> Optional[str]:
        """Extract cuisine type from place type string"""
        cuisine_keywords = {
            'vietnamese': 'Vietnamese',
            'japan': 'Japanese',
            'sushi': 'Japanese',
            'ramen': 'Japanese',
            'chinese': 'Chinese',
            'korean': 'Korean',
            'thai': 'Thai',
            'indian': 'Indian',
            'italian': 'Italian',
            'french': 'French',
            'american': 'American',
            'mexican': 'Mexican',
            'bbq': 'BBQ',
            'seafood': 'Seafood',
            'vegetarian': 'Vegetarian'
        }
        
        place_type_lower = place_type_str.lower()
        for keyword, cuisine in cuisine_keywords.items():
            if keyword in place_type_lower:
                return cuisine
        
        return None
    
    @staticmethod
    def _extract_cuisine_from_types(types: List[str]) -> Optional[str]:
        """Extract cuisine from Google types array"""
        for type_ in types:
            cuisine = DiningPlaceTransformer._extract_cuisine_type(type_)
            if cuisine:
                return cuisine
        return None
    
    @staticmethod
    def _convert_price_symbol_to_vnd(price_symbol: str) -> Optional[int]:
        """Convert price symbols ($$, $$$) to VND range"""
        price_map = {
            '$': 30000,      # Budget: 30k
            '$$': 80000,     # Moderate: 80k
            '$$$': 150000,   # Expensive: 150k
            '$$$$': 300000   # Very Expensive: 300k
        }
        return price_map.get(price_symbol)
    
    @staticmethod
    def _convert_price_level_to_vnd(price_level: Optional[int]) -> Optional[int]:
        """Convert Google price_level (0-4) to VND"""
        if price_level is None:
            return None
        
        price_map = {
            0: 20000,    # Free
            1: 50000,    # Inexpensive: 50k
            2: 100000,   # Moderate: 100k
            3: 200000,   # Expensive: 200k
            4: 400000    # Very Expensive: 400k
        }
        return price_map.get(price_level, 100000)
    
    @staticmethod
    def _parse_hours(hours_str: str) -> tuple:
        """Parse hours string to (open_time, close_time)"""
        # Example: "7:00 AM - 11:00 PM"
        if not hours_str or '-' not in hours_str:
            return None, None
        
        try:
            parts = hours_str.split('-')
            if len(parts) == 2:
                open_time = DiningPlaceTransformer._convert_12h_to_24h(parts[0].strip())
                close_time = DiningPlaceTransformer._convert_12h_to_24h(parts[1].strip())
                return open_time, close_time
        except:
            pass
        
        return None, None
    
    @staticmethod
    def _parse_google_hours(weekday_text: List[str]) -> tuple:
        """Parse Google weekday_text to extract hours"""
        if not weekday_text:
            return None, None
        
        # Get Monday hours (first day)
        monday_hours = weekday_text[0] if weekday_text else ""
        # Example: "Monday: 7:00 AM - 11:00 PM"
        
        if ':' in monday_hours:
            time_part = monday_hours.split(':', 1)[1].strip()
            return DiningPlaceTransformer._parse_hours(time_part)
        
        return None, None
    
    @staticmethod
    def _convert_12h_to_24h(time_str: str) -> Optional[str]:
        """Convert 12-hour format to 24-hour format"""
        try:
            from datetime import datetime
            # Parse "7:00 AM" → "07:00"
            time_obj = datetime.strptime(time_str, "%I:%M %p")
            return time_obj.strftime("%H:%M")
        except:
            return None


# ========================================
# Convenience Functions
# ========================================

def transform_api_response(api_data: Dict[str, Any], source: str = 'serpapi') -> Optional[DiningPlace]:
    """
    Hàm tiện ích để transform API response
    
    Args:
        api_data: Dict từ API
        source: 'serpapi' hoặc 'google'
    
    Returns:
        DiningPlace object
    """
    transformer = DiningPlaceTransformer()
    
    if source == 'serpapi':
        return transformer.from_serpapi_to_model(api_data)
    elif source == 'google':
        return transformer.from_google_to_model(api_data)
    else:
        logger.error(f"Unknown source: {source}")
        return None


if __name__ == '__main__':
    # Test transformer
    sample_serpapi_data = {
        "title": "Phở 24",
        "address": "5 Nguyễn Thiệp, Quận 1, TPHCM",
        "rating": 4.5,
        "reviews": 1200,
        "type": "Vietnamese restaurant",
        "price": "$$",
        "gps_coordinates": {"latitude": 10.774, "longitude": 106.702}
    }
    
    dining_place = transform_api_response(sample_serpapi_data, 'serpapi')
    
    if dining_place:
        print("✅ Transformation successful!")
        print(f"Name: {dining_place.name}")
        print(f"Cuisine: {dining_place.cuisineType}")
        print(f"Price: {dining_place.priceRangeVnd:,} VNĐ")
        print(f"Rating: {dining_place.rating} ⭐")
        print(f"Address: {dining_place.get_full_address()}")
