#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dining Place API Service - Lấy dữ liệu địa điểm ăn uống từ các API
"""

import requests
import logging
from typing import List, Dict, Optional, Any
from api_config import (
    SERPAPI_KEY, SERPAPI_BASE_URL,
    GOOGLE_MAPS_API_KEY, GOOGLE_PLACES_API_URL, GOOGLE_PLACE_DETAILS_URL,
    DEFAULT_SEARCH_PARAMS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiningPlaceAPIService:
    """Service để lấy dữ liệu dining places từ external APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize API service
        
        Args:
            api_key: API key (SERPAPI hoặc Google Maps)
                    Nếu không truyền, sẽ tự động lấy từ config
        """
        self.serpapi_key = api_key or SERPAPI_KEY
        self.google_key = api_key or GOOGLE_MAPS_API_KEY
        self.session = requests.Session()
        
        logger.info(f"DiningPlaceAPIService initialized")
        logger.info(f"SERPAPI: {'✅' if self.serpapi_key else '❌'}")
        logger.info(f"Google Maps: {'✅' if self.google_key else '❌'}")
    
    def search_restaurants_serpapi(
        self,
        query: str,
        location: str = "Ho Chi Minh City, Vietnam",
        radius: int = 5000,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm nhà hàng qua SERPAPI (Google Maps scraping)
        
        Args:
            query: Từ khóa tìm kiếm (VD: "phở", "japanese restaurant")
            location: Địa điểm (VD: "Ho Chi Minh City, Vietnam")
            radius: Bán kính tìm kiếm (mét)
            limit: Số lượng kết quả tối đa
        
        Returns:
            List[Dict]: Danh sách restaurants với full data
        
        Example:
            >>> service = DiningPlaceAPIService()
            >>> results = service.search_restaurants_serpapi("phở", "Quận 1, TPHCM")
            >>> print(len(results))
            20
        """
        if not self.serpapi_key:
            logger.error("SERPAPI key not configured!")
            return []
        
        try:
            params = {
                'engine': 'google_maps',
                'q': query,
                'type': 'search',
                'll': location,  # location
                'hl': 'vi',  # Vietnamese
                'api_key': self.serpapi_key,
                'num': limit
            }
            
            logger.info(f"Searching SERPAPI: query='{query}', location='{location}'")
            response = self.session.get(SERPAPI_BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('local_results', [])
            
            logger.info(f"Found {len(results)} results from SERPAPI")
            return results
            
        except Exception as e:
            logger.error(f"Error searching SERPAPI: {e}")
            return []
    
    def search_restaurants_google(
        self,
        lat: float,
        lng: float,
        keyword: str = "restaurant",
        radius: int = 5000,
        type_: str = "restaurant"
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm nhà hàng qua Google Places API
        
        Args:
            lat: Latitude
            lng: Longitude
            keyword: Từ khóa (VD: "phở", "sushi")
            radius: Bán kính (mét)
            type_: Loại place (restaurant, cafe, bar)
        
        Returns:
            List[Dict]: Danh sách restaurants
        """
        if not self.google_key:
            logger.error("Google Maps API key not configured!")
            return []
        
        try:
            params = {
                'location': f'{lat},{lng}',
                'radius': radius,
                'keyword': keyword,
                'type': type_,
                'language': 'vi',
                'key': self.google_key
            }
            
            logger.info(f"Searching Google Places: keyword='{keyword}', lat={lat}, lng={lng}")
            response = self.session.get(GOOGLE_PLACES_API_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"Google API error: {data.get('status')}")
                return []
            
            results = data.get('results', [])
            logger.info(f"Found {len(results)} results from Google Places")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Google Places: {e}")
            return []
    
    def get_place_details_google(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chi tiết của một place từ Google Places API
        
        Args:
            place_id: Google Place ID
        
        Returns:
            Dict: Chi tiết place hoặc None
        """
        if not self.google_key:
            logger.error("Google Maps API key not configured!")
            return None
        
        try:
            params = {
                'place_id': place_id,
                'language': 'vi',
                'fields': 'name,formatted_address,geometry,rating,user_ratings_total,'
                         'price_level,opening_hours,formatted_phone_number,website,'
                         'photos,types,reviews',
                'key': self.google_key
            }
            
            response = self.session.get(GOOGLE_PLACE_DETAILS_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"Google API error: {data.get('status')}")
                return None
            
            return data.get('result', {})
            
        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return None
    
    def search_by_coordinates(
        self,
        lat: float,
        lng: float,
        cuisine_type: Optional[str] = None,
        radius: int = 5000,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm nhà hàng theo tọa độ GPS
        
        Args:
            lat: Latitude
            lng: Longitude
            cuisine_type: Loại món ăn (Vietnamese, Japanese, etc.)
            radius: Bán kính (mét)
            limit: Số lượng kết quả
        
        Returns:
            List[Dict]: Danh sách restaurants
        """
        keyword = f"{cuisine_type} restaurant" if cuisine_type else "restaurant"
        
        # Try Google first (more reliable)
        if self.google_key:
            return self.search_restaurants_google(lat, lng, keyword, radius)
        
        # Fallback to SERPAPI
        if self.serpapi_key:
            location = f"@{lat},{lng},{radius}m"
            return self.search_restaurants_serpapi(keyword, location, radius, limit)
        
        logger.error("No API keys configured!")
        return []
    
    def search_by_address(
        self,
        address: str,
        cuisine_type: Optional[str] = None,
        radius: int = 5000,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm nhà hàng theo địa chỉ
        
        Args:
            address: Địa chỉ (VD: "Quận 1, TPHCM")
            cuisine_type: Loại món ăn
            radius: Bán kính
            limit: Số lượng kết quả
        
        Returns:
            List[Dict]: Danh sách restaurants
        """
        query = f"{cuisine_type} restaurant" if cuisine_type else "restaurant"
        
        if self.serpapi_key:
            return self.search_restaurants_serpapi(query, address, radius, limit)
        
        # TODO: Convert address to lat/lng using Google Geocoding
        logger.warning("Address search requires SERPAPI or Geocoding")
        return []


# ========================================
# Helper Functions
# ========================================

def search_dining_places(
    query: str = "restaurant",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    address: Optional[str] = None,
    cuisine_type: Optional[str] = None,
    radius: int = 5000,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Hàm tiện ích để tìm kiếm dining places
    
    Args:
        query: Từ khóa tìm kiếm
        lat, lng: Tọa độ GPS
        address: Địa chỉ
        cuisine_type: Loại món ăn
        radius: Bán kính (mét)
        limit: Số lượng kết quả
    
    Returns:
        List[Dict]: Danh sách restaurants
    
    Example:
        >>> # Tìm theo tọa độ
        >>> results = search_dining_places(lat=10.762622, lng=106.660172, cuisine_type="Vietnamese")
        
        >>> # Tìm theo địa chỉ
        >>> results = search_dining_places(address="Quận 1, TPHCM", query="phở")
    """
    service = DiningPlaceAPIService()
    
    if lat and lng:
        return service.search_by_coordinates(lat, lng, cuisine_type, radius, limit)
    elif address:
        return service.search_by_address(address, cuisine_type, radius, limit)
    else:
        logger.error("Must provide either coordinates (lat, lng) or address")
        return []


if __name__ == '__main__':
    # Test the service
    service = DiningPlaceAPIService()
    
    # Test search
    results = search_dining_places(
        lat=10.762622,
        lng=106.660172,
        cuisine_type="Vietnamese",
        radius=2000,
        limit=10
    )
    
    print(f"\nFound {len(results)} restaurants")
    for i, place in enumerate(results[:3], 1):
        print(f"\n{i}. {place.get('title', place.get('name', 'N/A'))}")
        print(f"   Address: {place.get('address', place.get('vicinity', 'N/A'))}")
        print(f"   Rating: {place.get('rating', 'N/A')}")
