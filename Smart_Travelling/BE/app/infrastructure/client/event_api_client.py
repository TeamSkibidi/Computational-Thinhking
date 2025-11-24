import requests
from datetime import datetime, date, time
from typing import List

from app.domain.entities.event import Event 

class EventAPIClient: 
    def __init__ (self, base_url: str, source_name: str = "external_api"):
        self.base_url = base_url.rstrip("/")
        self.source_name = source_name
    
    def _fetch_event (self, city: str, target_date: date) -> List[Event]:
        """
        Gọi API ngoài và map JSON → List[Event] (chưa lưu DB).
        """
        url = f"{self.base_url}/events"
        params = {
             "city": city,
             "date": target_date.isoformat(),
         }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status () #Kiểm tra lỗi HTTP: Kiểm tra mã trạng thái (status code) của phản hồi
        data = response.json() # Chuyển nội dung phản hồi từ API (là một chuỗi JSON) thành một đối tượng
       
        events: List[Event] = []

    #  def fetch_events(self, city: str, target_date: date) -> List[Event]:
        #  start_dt = datetime.combine(target_date, time(19, 30))
        # #  end_dt = datetime.combine(target_date, time(22, 0))
    #     return [
    #         Event(
    #             id=None,
    #             external_id="mock_1",
    #             name="Lễ hội pháo hoa Đà Nẵng (mock)",
    #             city=city,
    #             region="beach_area",
    #             lat=16.0678,
    #             lng=108.2208,
    #             start_datetime=start_dt,
    #             end_datetime=end_dt,
    #             session="evening",
    #             summary="Sự kiện mock để test luồng sync.",
    #             activities=["fireworks", "music"],
    #             image_url=None,
    #             price_vnd=200000,
    #             popularity=90,
    #             source=self.source_name,
    #         )
    #     ]