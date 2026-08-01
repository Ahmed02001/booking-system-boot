# api_client.py
import json
import random
import requests
import urllib3
from typing import Dict, List, Optional, Tuple
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MyVisitAPIClient:
    """عميل API للتعامل مع نظام MyVisit"""
    
    def __init__(self, base_url: str, api_key: str, app_name: str):
        self.base_url = base_url
        self.api_key = api_key
        self.app_name = app_name
        self.session = requests.Session()
        self.session.verify = False
        
    def _get_headers(self, additional_headers: Dict = None) -> Dict:
        """بناء رؤوس الطلبات الأساسية"""
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ar",
            "application-api-key": self.api_key,
            "application-name": self.app_name,
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://minhal.myvisit.com",
            "referer": "https://minhal.myvisit.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers
    
    def _get_cookies_from_headers(self, headers: Dict) -> Dict:
        """استخراج الكوكيز من الرؤوس"""
        cookie_str = headers.get("cookie", "")
        cookies = {}
        for item in cookie_str.split("; "):
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key] = value
        return cookies
    
    def prepare_visit(self, service_id: int, headers: Dict, proxy: str = None) -> Tuple[bool, Dict]:
        """مرحلة تحضير الزيارة - PrepareVisit"""
        url = f"{self.base_url}/CentralAPI/Service/{service_id}/PrepareVisit"
        
        req_headers = self._get_headers(headers)
        cookies = self._get_cookies_from_headers(headers)
        
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        try:
            response = self.session.post(
                url,
                headers=req_headers,
                cookies=cookies,
                proxies=proxies,
                timeout=120,
                data="{}"
            )
            
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}"}
            
            data = response.json()
            if not data.get("Success"):
                return False, {"error": data.get("ErrorMessage", "Unknown error")}
            
            prepared_data = data.get("Data", {})
            return True, {
                "prepared_visit_id": prepared_data.get("PreparedVisitId"),
                "prepared_visit_token": prepared_data.get("PreparedVisitToken"),
                "user_id": prepared_data.get("UserId"),
                "raw_data": data
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def search_available_dates(self, service_id: int, start_date: str, headers: Dict, proxy: str = None) -> Tuple[bool, List[Dict]]:
        """البحث عن التواريخ المتاحة"""
        url = f"{self.base_url}/CentralAPI/SearchAvailableDates"
        
        params = {
            "maxResults": 31,
            "serviceId": service_id,
            "startDate": start_date
        }
        
        req_headers = self._get_headers(headers)
        cookies = self._get_cookies_from_headers(headers)
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        try:
            response = self.session.get(
                url,
                headers=req_headers,
                cookies=cookies,
                proxies=proxies,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                return False, []
            
            data = response.json()
            if not data.get("Success"):
                return False, []
            
            return True, data.get("Results", [])
            
        except Exception:
            return False, []
    
    def search_available_slots(self, calendar_id: int, service_id: int, headers: Dict, proxy: str = None) -> Tuple[bool, List[Dict]]:
        """البحث عن الساعات المتاحة"""
        url = f"{self.base_url}/CentralAPI/SearchAvailableSlots"
        
        params = {
            "CalendarId": calendar_id,
            "ServiceId": service_id,
            "dayPart": 0
        }
        
        req_headers = self._get_headers(headers)
        cookies = self._get_cookies_from_headers(headers)
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        try:
            response = self.session.get(
                url,
                headers=req_headers,
                cookies=cookies,
                proxies=proxies,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                return False, []
            
            data = response.json()
            if not data.get("Success"):
                return False, []
            
            return True, data.get("Results", [])
            
        except Exception:
            return False, []
    
    def book_appointment(self, service_id: int, appointment_date: str, appointment_time: int,
                         prepared_visit_id: int, prepared_token: str, 
                         headers: Dict, proxy: str = None, position: str = None) -> Tuple[bool, Dict]:
        """مرحلة تأكيد الحجز - AppointmentSet"""
        url = f"{self.base_url}/CentralAPI/AppointmentSet"
        
        if not position:
            position = "%7B%22lat%22%3A%2232.0804%22%2C%22lng%22%3A%2234.7807%22%2C%22accuracy%22%3A1440%7D"
        
        params = {
            "ServiceId": service_id,
            "appointmentDate": f"{appointment_date}T00:00:00",
            "appointmentTime": appointment_time,
            "position": position,
            "preparedVisitId": prepared_visit_id
        }
        
        req_headers = self._get_headers(headers)
        req_headers["PreparedVisitToken"] = str(prepared_token)
        req_headers["preparedvisittoken"] = str(prepared_token)
        
        cookies = self._get_cookies_from_headers(headers)
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        try:
            response = self.session.get(
                url,
                headers=req_headers,
                cookies=cookies,
                proxies=proxies,
                params=params,
                timeout=120
            )
            
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}"}
            
            data = response.json()
            if not data.get("Success"):
                return False, {"error": data.get("ErrorMessage", "Unknown error"), "messages": data.get("Messages")}
            
            results = data.get("Results", {})
            return True, {
                "location_name": results.get("LocationName", ""),
                "reference_date": results.get("ReferenceDate", ""),
                "raw_data": data
            }
            
        except Exception as e:
            return False, {"error": str(e)}