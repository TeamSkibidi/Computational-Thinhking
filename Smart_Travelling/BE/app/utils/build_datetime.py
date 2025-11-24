import re
from datetime import datetime 
from typing import Optional
from .format_time import format_time

def build_datetime (date_str: Optional[str], time_str: Optional[str]) -> Optional[datetime]:
    if not date_str or not time_str:
        return None
    
    t = format_time (time_str)
    if not t: 
        raise ValueError("Giờ không hợp lệ: {time_str}")
    
    return datetime.fromisoformat(f"{date_str}T{t}:00")
