#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Configuration - Cấu hình API keys và endpoints
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ========================================
# SERPAPI Configuration (Google Places API)
# ========================================
SERPAPI_KEY = os.getenv('SERPAPI_API_KEY', '')
SERPAPI_BASE_URL = 'https://serpapi.com/search'

# ========================================
# Google Maps API Configuration
# ========================================
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
GOOGLE_PLACES_API_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
GOOGLE_PLACE_DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'

# ========================================
# Yelp Fusion API Configuration
# ========================================
YELP_API_KEY = os.getenv('YELP_API_KEY', '')
YELP_API_URL = 'https://api.yelp.com/v3/businesses/search'

# ========================================
# Foursquare API Configuration
# ========================================
FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY', '')
FOURSQUARE_API_URL = 'https://api.foursquare.com/v3/places/search'

# ========================================
# Default Search Parameters
# ========================================
DEFAULT_SEARCH_PARAMS = {
    'radius': 5000,  # 5km radius
    'language': 'vi',  # Vietnamese
    'type': 'restaurant',
    'limit': 20
}

# ========================================
# Rate Limiting
# ========================================
API_RATE_LIMIT = {
    'serpapi': 100,  # requests per hour
    'google': 1000,  # requests per day
    'yelp': 500,  # requests per day
    'foursquare': 950  # requests per day
}

# ========================================
# Helper Functions
# ========================================

def validate_api_keys():
    """Kiểm tra xem các API keys đã được cấu hình chưa"""
    keys = {
        'SERPAPI': SERPAPI_KEY,
        'Google Maps': GOOGLE_MAPS_API_KEY,
        'Yelp': YELP_API_KEY,
        'Foursquare': FOURSQUARE_API_KEY
    }
    
    available = {}
    for name, key in keys.items():
        available[name] = bool(key)
    
    return available

def get_active_api():
    """Lấy API đang hoạt động (ưu tiên theo thứ tự)"""
    if SERPAPI_KEY:
        return 'serpapi'
    elif GOOGLE_MAPS_API_KEY:
        return 'google'
    elif YELP_API_KEY:
        return 'yelp'
    elif FOURSQUARE_API_KEY:
        return 'foursquare'
    return None

if __name__ == '__main__':
    print("API Configuration Status:")
    print("=" * 50)
    keys = validate_api_keys()
    for name, available in keys.items():
        status = "✅ Configured" if available else "❌ Not configured"
        print(f"{name:15} : {status}")
    
    print("\n" + "=" * 50)
    active = get_active_api()
    if active:
        print(f"Active API: {active}")
    else:
        print("⚠️ No API keys configured!")
