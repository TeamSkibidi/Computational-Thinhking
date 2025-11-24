def format_money(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value:,.0f} VNĐ".replace(",", ".")
