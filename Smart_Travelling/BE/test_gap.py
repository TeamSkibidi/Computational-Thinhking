from app.api.schemas.itinerary_request import ItineraryRequest, BlockTimeConfig
from app.application.services.trip_service import get_trip_itinerary
from datetime import date

# Tạo request với blocks enabled
req = ItineraryRequest(
    city='Hồ Chí Minh',
    start_date=date(2025, 12, 10),
    num_days=1,
    morning=BlockTimeConfig(enabled=True, start='08:00', end='11:30'),
    lunch=BlockTimeConfig(enabled=True, start='11:30', end='13:00'),
    afternoon=BlockTimeConfig(enabled=True, start='13:30', end='17:30'),
    dinner=BlockTimeConfig(enabled=True, start='18:00', end='19:30'),
    evening=BlockTimeConfig(enabled=True, start='20:00', end='22:00'),
)

result = get_trip_itinerary(req)
days = result.get('days', [])

result = get_trip_itinerary(req)
days = result.get('days', [])

if days:
    day = days[0]
    print('=== DAY 1 SCHEDULE ===')
    for block_name, items in day.get('blocks', {}).items():
        print(f'\n--- {block_name.upper()} ({len(items)} items) ---')
        prev_end = None
        for item in items:
            name = item.get('name', 'N/A')
            if name and len(name) > 40:
                name = name[:40] + '...'
            start = item.get('start', 'N/A')
            end = item.get('end', 'N/A')
            dwell = item.get('dwell_min', 0)
            travel = item.get('travel_from_prev_min', 0)
            
            # Tính gap
            if prev_end:
                h1, m1 = map(int, prev_end.split(':'))
                h2, m2 = map(int, start.split(':'))
                gap = (h2 * 60 + m2) - (h1 * 60 + m1)
                if gap > travel + 5:
                    print(f"  ⚠️ GAP: {gap - travel} phút rảnh!")
            
            print(f"  {start} - {end}: {name} (dwell: {dwell}, travel: {travel})")
            prev_end = end
else:
    print('No result:', result)
