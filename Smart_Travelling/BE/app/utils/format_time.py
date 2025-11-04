import re

_TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")

def format_time(value: str | None) -> str | None:
    if not value:
        return None
    if not _TIME_RE.match(value):
        return None
    hh, mm = map(int, value.split(":"))
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return f"{hh:02d}:{mm:02d}"
    return None
