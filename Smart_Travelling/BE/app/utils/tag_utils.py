from typing import Optional
from app.domain.entities.itinerary_spot import ItinerarySpot
from app.application.itinerary.trip_context import UserPreferences

""" Tính điểm tag cho 1 địa điểm dựa trên sở thích người dùng """
def tag_score(spot: ItinerarySpot, prefs: Optional[UserPreferences]) -> int: 
    if prefs is None:
        return 0;
    score = 0
    for tag in spot.tags:
        if tag in prefs.preferred_tags:
            score += 1
        if tag in prefs.avoid_tags:
            score -= 1
    return score

""" Loại những tag mà người dùng không thích """
def apply_tag_filter(
    spots: list[ItinerarySpot],
    prefs: Optional[UserPreferences]
) -> list[ItinerarySpot]:
    if not spots:
        return []

    if not prefs:
        return spots

    result = spots

    if prefs.avoid_tags:
        avoid = set(prefs.avoid_tags)
        result = [
            s for s in result
            if (set(s.tags or []).isdisjoint(avoid))
        ]

    if prefs.preferred_tags:
        preferred = set(prefs.preferred_tags)
        with_preferred = [
            s for s in result
            if not preferred.isdisjoint(set(s.tags or []))
        ]
        # Nếu còn điểm match tag → dùng list này, ngược lại giữ nguyên result
        if with_preferred:
            result = with_preferred

    return result


""" Sắp xếp địa điểm theo sở thích người dùng, rating và popularity """
def visit_sort_key(spot, prefs, must_ids):
    return (
        1 if spot.id in must_ids else 0,
        tag_score(spot, prefs),
        spot.rating or 0.0,
        spot.popularity or 0,
    )