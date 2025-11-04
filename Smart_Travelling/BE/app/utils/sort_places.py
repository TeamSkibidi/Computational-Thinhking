def sort_places(places, sort_by: str):
    keyers = {
        "price_asc":   lambda p: (p.priceVnd is None, p.priceVnd),
        "price_desc":  lambda p: (p.priceVnd is None, -(p.priceVnd or 0)),
        "rating_desc": lambda p: (p.rating is None, -(p.rating or 0)),
        "open_time":   lambda p: (p.openTime is None, p.openTime or "99:99"),
        "popular_desc":lambda p: (p.popularity is None, -(p.popularity or 0)),
    }
    k = keyers.get(sort_by, keyers["popular_desc"])
    return sorted(places, key=k)
