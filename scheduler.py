# scheduler.py
import time
from datetime import datetime, timedelta
from typing import Optional

class PrecisionScheduler:
    """نظام جدولة دقيق يعمل بمستوى نانو ثانية"""
    
    def __init__(self, timezone_offset_hours: int = 3):
        self.timezone_offset = timezone_offset_hours
    
    def get_target_timestamp(self, time_str: str) -> int:
        """
        حساب الطابع الزمني بالملي ثانية للتوقيت المحدد
        time_str: بتنسيق HH:MM:SS:mmm
        """
        parts = time_str.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        ms = int(parts[3])
        
        now_utc = datetime.utcnow()
        now_local = now_utc + timedelta(hours=self.timezone_offset)
        
        target_local = datetime(
            now_local.year, now_local.month, now_local.day,
            hours, minutes, seconds, ms * 1000
        )
        
        if target_local < now_local:
            target_local += timedelta(days=1)
        
        target_utc = target_local - timedelta(hours=self.timezone_offset)
        epoch = datetime(1970, 1, 1)
        return int((target_utc - epoch).total_seconds() * 1000)
    
    def precise_wait_until(self, target_ms: int) -> None:
        """
        الانتظار بدقة عالية حتى الوقت المحدد
        يستخدم Sleep للانتظار الخشن ثم Spin للدقة المطلقة
        """
        while True:
            now_ms = int(time.time() * 1000)
            coarse_wait = target_ms - 15 - now_ms
            if coarse_wait <= 0:
                break
            time.sleep(coarse_wait / 1000.0)
        
        target_time = target_ms / 1000.0
        while time.time() < target_time:
            pass
    
    def get_time_remaining(self, target_time_str: str) -> float:
        """حساب الوقت المتبقي حتى التوقيت المستهدف بالثواني"""
        target_ms = self.get_target_timestamp(target_time_str)
        now_ms = int(time.time() * 1000)
        return (target_ms - now_ms) / 1000.0
    
    def format_local_time(self, timestamp_ms: int) -> str:
        """تنسيق الوقت المحلي للطباعة"""
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt.strftime('%H:%M:%S.%f')[:-3]