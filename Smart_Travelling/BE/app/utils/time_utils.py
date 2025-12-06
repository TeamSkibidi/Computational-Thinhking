from datetime import time as dt_time
from typing import Optional


def time_str_to_minutes(time_str: str) -> int:
    """Tách giờ và phút ra thành 2 biến số"""
    hours, minutes = map(int, time_str.split(":")) 
    return hours * 60 + minutes

def time_to_min(t) -> Optional[int]:
    """Convert time/int sang minutes."""
    if t is None:
        return None
    if isinstance(t, int):
        return t
    if isinstance(t, dt_time):
        return t.hour * 60 + t.minute
    return None

def min_to_time_str(minutes: int) -> str:
    hour = minutes // 60
    minute = minutes % 60
    """ Chuyển về định dạng HH:MM   """
    return f"{hour:02d}:{minute:02d}"