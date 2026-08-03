# config.py
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")


class Config:
    # ===== إعدادات الوقت =====
    TIMEZONE_OFFSET_HOURS = int(os.getenv("TIMEZONE_OFFSET_HOURS", "3"))

    # أوقات الجدولة (بتنسيق HH:MM:SS:mmm)
    PREPARE_LAUNCH_TIME = os.getenv("PREPARE_LAUNCH_TIME", "14:50:56:000")
    BOOKING_LAUNCH_TIME = os.getenv("BOOKING_LAUNCH_TIME", "14:55:48:500")

    # ===== إعدادات إعادة المحاولة =====
    RETRY_ENABLED = os.getenv("RETRY_ENABLED", "true").lower() == "true"
    RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "2"))
    MAX_RETRY_ROUNDS = int(os.getenv("MAX_RETRY_ROUNDS", "2"))

    # ===== إعدادات الأداء =====
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "50"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

    # ===== إعدادات التشغيل =====
    AUTO_LAUNCH_ENABLED = os.getenv("AUTO_LAUNCH_ENABLED", "true").lower() == "true"

    # ===== إعدادات الإيميل =====
    SEND_EMAILS = os.getenv("SEND_EMAILS", "true").lower() == "true"
    SEND_SUMMARY_EMAIL = os.getenv("SEND_SUMMARY_EMAIL", "true").lower() == "true"
    EMAIL_CONFIG_FILE = os.getenv("EMAIL_CONFIG_FILE", "email_config.json")
    EMAIL_DELAY_SECONDS = int(os.getenv("EMAIL_DELAY_SECONDS", "1"))

    # ===== مسارات الملفات =====
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database_backup.json")
    PROXIES_PATH = os.getenv("PROXIES_PATH", "prox_tested.json")
    SLOTS_PATH = os.getenv("SLOTS_PATH", "sloty.txt")
    RESULTS_DIR = os.getenv("RESULTS_DIR", "results")

    # ===== إعدادات API =====
    BASE_URL = os.getenv("API_BASE_URL", "https://central.myvisit.com")
    API_KEY = os.getenv("API_KEY", "8640a12d-52a7-4c2a-afe1-4411e00e3ac4")
    APPLICATION_NAME = os.getenv("APPLICATION_NAME", "minhal_ezrahi")

    @classmethod
    def project_root(cls) -> str:
        return str(Path(__file__).resolve().parent)

    @classmethod
    def resolve_path(cls, relative_path: Optional[str] = None) -> str:
        if not relative_path:
            return cls.project_root()

        path = Path(relative_path)
        if path.is_absolute():
            return str(path)

        return str((Path(cls.project_root()) / path).resolve())

    @classmethod
    def get_target_date(cls, date_str: Optional[str] = None):
        """الحصول على تاريخ الحجز المستهدف"""
        if date_str:
            return date_str
        return datetime.now().strftime("%Y-%m-%d")