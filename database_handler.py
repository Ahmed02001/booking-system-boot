# database_handler.py
import json
from typing import List, Dict, Optional

class DatabaseHandler:
    """التعامل مع قاعدة بيانات الزبائن"""
    
    @staticmethod
    def load_clients(db_path: str) -> List[Dict]:
        """تحميل كافة الزبائن الصالحين من قاعدة البيانات"""
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                clients = json.load(f)
        except FileNotFoundError:
            return []
        
        filtered = []
        for c in clients:
            if c.get("id_number") and c.get("service_id") and c.get("parsed_header"):
                headers = c.get("parsed_header", {}).copy()
                filtered.append({
                    "id_number": c.get("id_number"),
                    "service_id": c.get("service_id"),
                    "headers": headers,
                    "email": c.get("email", ""),  # إضافة الإيميل
                    "name": c.get("name", "")  # إضافة الاسم
                })
        return filtered
    
    @staticmethod
    def load_proxies(proxies_path: str) -> List[Dict]:
        """تحميل البروكسيات الناجحة وترتيبها حسب البينج"""
        try:
            with open(proxies_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return []
        
        successful = [r for r in data if r.get("proxy")]
        successful.sort(key=lambda x: x.get("ping_ms", 9999))
        return successful
    
    @staticmethod
    def load_slots(slots_path: str) -> Dict[str, List[int]]:
        """تحميل خريطة الساعات من ملف sloty.txt"""
        try:
            with open(slots_path, 'r', encoding='utf-8') as f:
                slots_map = json.load(f)
            
            result = {}
            for service_id, times in slots_map.items():
                result[str(service_id)] = [int(s) for s in times if str(s).isdigit()]
            return result
        except Exception:
            return {}
    
    @staticmethod
    def save_results(results: List[Dict], output_path: str) -> None:
        """حفظ النتائج في ملف نصي"""
        with open(output_path, 'w', encoding='utf-8') as f:
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
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)