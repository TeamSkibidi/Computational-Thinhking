from pydantic import BaseModel, Field, model_validator
from typing import Optional

class Address(BaseModel):
    formatted: str = Field(..., min_length=3, strip_whitespace=True,
                           example="26 Lê Thị Riêng, Q.1, TP.HCM")
    lat: Optional[float] = Field(None, ge=-90, le=90, example=10.7756)
    lng: Optional[float] = Field(None, ge=-180, le=180, example=106.6903)

    @model_validator(mode="after")
    def _lat_lng_pair(cls, values: "Address"):
        # Nếu một trong hai có, thì cả hai phải có
        if (values.lat is None) ^ (values.lng is None):
            raise ValueError("lat và lng phải cùng có hoặc cùng vắng")
        return values
import unicodedata
import re

def norm_vi(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("Đ", "D").replace("đ", "d")  # xử lý đặc thù TV
    s = s.casefold()  # mạnh hơn lower() cho nhiều ngôn ngữ
    s = re.sub(r"\s+", " ", s).strip()  # (tuỳ chọn) gom khoảng trắng
    return s