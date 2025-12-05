from typing import List
from app.adapters.repositories import tag_repository

# Lấy tất cả địa điểm theo tag
def get_all_places_by_tag() -> List[dict]:
    return tag_repository.fetch_tags_by_data()