import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)

# =======================================================
# Helper: lấy message an toàn
# =======================================================
def extract_message(body):
    return body.get("message") or body.get("error_message") or ""


# =======================================================
# TC01 – City hợp lệ, default k=5
# =======================================================
def test_valid_city_default_k():
    res = client.post("/api/v0/visitor/recommend", json={"city": "Hồ Chí Minh"})
    assert res.status_code == 200
    body = res.json()

    assert "data" in body
    places = body["data"].get("places", [])
    assert isinstance(places, list)
    assert len(places) == 5

    ids = [p.get("id") for p in places]
    assert None not in ids
    assert len(ids) == len(set(ids))
    
    
# =======================================================
# TC02 – seen_ids không được trả lại
# =======================================================
def test_seen_ids_filtering():
    seen = [1, 2, 3, 4, 5]
    res = client.post("/api/v0/visitor/recommend", json={"city": "Hồ Chí Minh", "seen_ids": seen})
    body = res.json()

    returned_ids = [p.get("id") for p in body["data"].get("places", [])]
    assert all(x not in set(seen) for x in returned_ids)






# =======================================================
# TC03 – city không có dữ liệu → trả về []
# =======================================================
def test_city_not_exist():
    res = client.post("/api/v0/visitor/recommend", json={"city": "Tokyo"})
    body = res.json()

    assert body["data"].get("places", []) == []





# =======================================================
# TC04 – seen_ids quá lớn → reset
# =======================================================
def test_seen_ids_reset():
    seen = list(range(1, 12))  # 11 IDs
    res = client.post("/api/v0/visitor/recommend",
                      json={"city": "Hồ Chí Minh", "seen_ids": seen, "k": 5})
    body = res.json()

    assert len(body["data"].get("places", [])) == 5





# =======================================================
# TC05 – nhập số
# =======================================================
def test_city_is_number():
    res = client.post("/api/v0/visitor/recommend", json={"city": "123"})
    body = res.json()

    assert body["data"].get("places", []) == []


# =======================================================
# TC6 – stress 50 lần
# =======================================================
def test_stress_requests():
    for _ in range(50):
        res = client.post("/api/v0/visitor/recommend", json={"city": "Hồ Chí Minh", "k": 5})
        assert res.status_code == 200
