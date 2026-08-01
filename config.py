# config.py
import os
from datetime import datetime, timedelta

class Config:
    # ===== إعدادات الوقت =====
    TIMEZONE_OFFSET_HOURS = 3  # UTC+3 للقدس الصيفي
    
    # أوقات الجدولة (بتنسيق HH:MM:SS:mmm)
    PREPARE_LAUNCH_TIME = "16:55:56:000"
    BOOKING_LAUNCH_TIME = "16:59:48:500"
    
    # ===== إعدادات إعادة المحاولة =====
    RETRY_ENABLED = True
    RETRY_DELAY_SECONDS = 2
    MAX_RETRY_ROUNDS = 2
    
    # ===== إعدادات الأداء =====
    MAX_WORKERS = 50  # الحد الأقصى للخيوط المتزامنة
    REQUEST_TIMEOUT = 120  # مهلة الطلب بالثواني
    
    # ===== إعدادات التشغيل =====
    AUTO_LAUNCH_ENABLED = True  # تفعيل الجدولة الزمنية
    
    # ===== إعدادات الإيميل =====
    SEND_EMAILS = True  # تفعيل/تعطيل إرسال الإيميلات
    SEND_SUMMARY_EMAIL = True  # إرسال إيميل تلخيصي للمشرف
    EMAIL_CONFIG_FILE = "email_config.json"
    EMAIL_DELAY_SECONDS = 1  # تأخير بين الإيميلات
    
    # ===== مسارات الملفات =====
    DATABASE_PATH = "database_backup.json"
    PROXIES_PATH = "prox_tested.json"
    SLOTS_PATH = "sloty.txt"
    RESULTS_DIR = "results"
    
    # ===== إعدادات API =====
    BASE_URL = "https://central.myvisit.com"
    API_KEY = "8640a12d-52a7-4c2a-afe1-4411e00e3ac4"
    APPLICATION_NAME = "minhal_ezrahi"
    
    @classmethod
    def get_target_date(cls, date_str=None):
        """الحصول على تاريخ الحجز المستهدف"""
        if date_str:
            return date_str
        # افتراضي: بعد 3 أيام من اليوم
        target = datetime.now() + timedelta(days=0)
        return target.strftime("%Y-%m-%d")