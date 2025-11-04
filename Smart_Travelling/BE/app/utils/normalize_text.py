import re
from unidecode import unidecode

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    
    if not isinstance(text, str):
        text = str(text)
    
    t = unidecode(text)
    t = t.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t
