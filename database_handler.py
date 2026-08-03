# database_handler.py
import json
from pathlib import Path
from typing import List, Dict

from config import Config


class DatabaseHandler:
    """التعامل مع قاعدة بيانات الزبائن"""

    @staticmethod
    def load_clients(db_path: str) -> List[Dict]:
        """تحميل كافة الزبائن الصالحين من قاعدة البيانات"""
        resolved_path = Config.resolve_path(db_path)
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                clients = json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

        filtered = []
        for c in clients:
            if not c.get("id_number") or not c.get("service_id"):
                continue

            headers = c.get("parsed_header") or c.get("headers") or {}
            if not isinstance(headers, dict):
                continue

            cookie = headers.get("cookie", "")
            if "your_cookie_here" in cookie.lower():
                continue

            filtered.append({
                "id_number": str(c.get("id_number")),
                "service_id": str(c.get("service_id")),
                "headers": headers,
                "email": c.get("email", ""),
                "name": c.get("name", "")
            })
        return filtered

    @staticmethod
    def load_proxies(proxies_path: str) -> List[Dict]:
        """تحميل البروكسيات الناجحة وترتيبها حسب البينج"""
        resolved_path = Config.resolve_path(proxies_path)
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        successful = [r for r in data if isinstance(r, dict) and r.get("proxy")]
        successful.sort(key=lambda x: x.get("ping_ms", 9999))
        return successful

    @staticmethod
    def load_slots(slots_path: str) -> Dict[str, List[int]]:
        """تحميل خريطة الساعات من ملف sloty.txt"""
        resolved_path = Config.resolve_path(slots_path)
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                slots_map = json.load(f)

            result = {}
            for service_id, times in slots_map.items():
                if isinstance(times, list):
                    result[str(service_id)] = [int(s) for s in times if str(s).isdigit()]
            return result
        except Exception:
            return {}

    @staticmethod
    def save_results(results: List[Dict], output_path: str) -> None:
        """حفظ النتائج في ملف نصي"""
        resolved_path = Config.resolve_path(output_path)
        Path(resolved_path).parent.mkdir(parents=True, exist_ok=True)

        with open(resolved_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("📊 نتائج الحجوزات\n")
            f.write("=" * 80 + "\n\n")

            for r in results:
                if r.get("success"):
                    f.write(f"✅ Client: {r['id_number']} | Service: {r['service_id']} | ")
                    f.write(f"Status: SUCCESS | Location: {r['location_name']} | ")
                    f.write(f"Date: {r['ref_date']} | Slot: {r.get('chosen_slot', 'N/A')}\n")
                else:
                    brief = r.get('error_msg', 'Unknown error')
                    if len(brief) > 80:
                        brief = brief[:77] + "..."
                    f.write(f"❌ Client: {r['id_number']} | Service: {r['service_id']} | ")
                    f.write(f"Status: FAILED | Reason: {brief}\n")

            f.write("\n" + "=" * 80 + "\n")
            total = len(results)
            success = sum(1 for r in results if r.get("success", False))
            f.write(f"📊 الإجمالي: ✅ نجح {success} | ❌ فشل {total - success}\n")
            f.write("=" * 80 + "\n")

    @staticmethod
    def save_results_json(results: List[Dict], output_path: str) -> None:
        """حفظ النتائج في ملف JSON"""
        resolved_path = Config.resolve_path(output_path)
        Path(resolved_path).parent.mkdir(parents=True, exist_ok=True)

        with open(resolved_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)