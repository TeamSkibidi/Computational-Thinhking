import math


""" Tính khoảng cách bằng tọa độ giữa 2 điểm (đường chim bay)"""
def haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0  
    print (lat1, lng1, lat2, lng2)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def estimate_travel_minutes(distance_km: float) -> int:

    return int(round(distance_km * 12))
