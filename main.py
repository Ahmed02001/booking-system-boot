# main.py
import sys
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from datetime import datetime

from web_app import app
from config import Config
from api_client import MyVisitAPIClient
from scheduler import PrecisionScheduler
from database_handler import DatabaseHandler
from email_sender import EmailSender

class BookingSystem:
    """النظام الرئيسي للحجز"""
    
    def __init__(self):
        self.config = Config()
        self.scheduler = PrecisionScheduler(self.config.TIMEZONE_OFFSET_HOURS)
        self.api_client = MyVisitAPIClient(
            base_url=self.config.BASE_URL,
            api_key=self.config.API_KEY,
            app_name=self.config.APPLICATION_NAME
        )
        self.db_handler = DatabaseHandler()
        self.email_sender = EmailSender(self.config.EMAIL_CONFIG_FILE)
        
        # تخزين النتائج
        self.results = {}
        self.clients = []
    
    def run_client_booking(self, client: Dict, proxy_info: Dict, slots: List[int],
                          target_date: str, prepare_target_ms: int, 
                          booking_target_ms: int, round_num: int = 1) -> Dict:
        """تنفيذ الحجز لزبون واحد"""
        id_number = client["id_number"]
        service_id = client["service_id"]
        headers = client["headers"]
        prefix = f"[جولة {round_num}][{id_number} - خدمة {service_id}]"
        
        # اختيار ساعة عشوائية
        chosen_slot = random.choice(slots) if slots else 530
        
        result = {
            "id_number": id_number,
            "service_id": service_id,
            "success": False,
            "location_name": "",
            "ref_date": "",
            "error_msg": "",
            "round": round_num,
            "chosen_slot": chosen_slot
        }
        
        proxy = proxy_info.get("proxy") if proxy_info else None
        position = proxy_info.get("position") if proxy_info else None
        
        try:
            # ── المرحلة 1: PrepareVisit ───────────────────────
            if self.config.AUTO_LAUNCH_ENABLED:
                time.sleep(random.randint(0, 100) / 1000.0)
            else:
                time.sleep(random.uniform(0.5, 1.5))
            
            success, prepare_data = self.api_client.prepare_visit(
                service_id=service_id,
                headers=headers,
                proxy=proxy
            )
            
            if not success:
                result["error_msg"] = f"فشل التحضير: {prepare_data.get('error', 'Unknown')}"
                print(f"❌ {prefix}: {result['error_msg']}")
                return result
            
            prepared_visit_id = prepare_data.get("prepared_visit_id")
            prepared_token = prepare_data.get("prepared_visit_token")
            
            print(f"✅ {prefix}: تم التحضير - معرف الزيارة: {prepared_visit_id} (الساعة: {chosen_slot})")
            
            # ── الانتظار الدقيق للمرحلة الثانية ──────────────
            if self.config.AUTO_LAUNCH_ENABLED:
                self.scheduler.precise_wait_until(booking_target_ms)
            else:
                time.sleep(random.uniform(2, 4))
            
            # ── المرحلة 2: AppointmentSet ─────────────────────
            time.sleep(random.randint(0, 250) / 1000.0)
            
            success, booking_data = self.api_client.book_appointment(
                service_id=service_id,
                appointment_date=target_date,
                appointment_time=chosen_slot,
                prepared_visit_id=prepared_visit_id,
                prepared_token=prepared_token,
                headers=headers,
                proxy=proxy,
                position=position
            )
            
            if success:
                result["success"] = True
                result["location_name"] = booking_data.get("location_name", "غير معروف")
                result["ref_date"] = booking_data.get("reference_date", "غير معروف")
                print(f"🎉 {prefix}: تم الحجز بنجاح! الموقع: {result['location_name']}")
            else:
                result["error_msg"] = booking_data.get("error", "خطأ غير معروف")
                print(f"❌ {prefix}: فشل الحجز: {result['error_msg']}")
                
        except Exception as e:
            result["error_msg"] = f"خطأ غير متوقع: {str(e)}"
            print(f"❌ {prefix}: {result['error_msg']}")
        
        return result
    
    def run_round(self, clients: List[Dict], proxies: List[Dict], 
                  slots_map: Dict, target_date: str,
                  prepare_target_ms: int, booking_target_ms: int,
                  round_num: int) -> None:
        """تشغيل جولة حجز متوازية"""
        if not clients:
            return
        
        workers = min(self.config.MAX_WORKERS, len(clients))
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            
            for i, client in enumerate(clients):
                proxy_info = proxies[i % len(proxies)] if proxies else None
                service_id = client["service_id"]
                client_slots = slots_map.get(str(service_id), [515, 520, 525, 530])
                
                future = executor.submit(
                    self.run_client_booking,
                    client, proxy_info, client_slots,
                    target_date, prepare_target_ms, booking_target_ms,
                    round_num
                )
                futures[future] = client
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        self.results[result["id_number"]] = result
                except Exception as e:
                    client = futures[future]
                    self.results[client["id_number"]] = {
                        "id_number": client["id_number"],
                        "service_id": client["service_id"],
                        "success": False,
                        "location_name": "",
                        "ref_date": "",
                        "error_msg": f"خطأ في الخيط: {str(e)}",
                        "round": round_num
                    }
    
    def get_failed_clients(self) -> List[Dict]:
        """الحصول على قائمة الزبائن الفاشلين"""
        failed = []
        for client in self.clients:
            result = self.results.get(client["id_number"], {})
            if not result.get("success", False):
                failed.append(client)
        return failed
    
    def run(self, target_date: str = None):
        """تشغيل النظام الرئيسي"""
        # تحميل البيانات
        self.clients = self.db_handler.load_clients(self.config.DATABASE_PATH)
        proxies = self.db_handler.load_proxies(self.config.PROXIES_PATH)
        slots_map = self.db_handler.load_slots(self.config.SLOTS_PATH)
        
        if not self.clients:
            print("❌ لا يوجد زبائن للتشغيل")
            return
        
        if not proxies:
            print("⚠️ لا توجد بروكسيات، سيتم التشغيل بدون بروكسي")
            proxies = [{"proxy": None, "ping_ms": 0}]
        
        target_date = target_date or self.config.get_target_date()
        
        print("═" * 60)
        print("⚡ نظام الحجز البرمجي المتزامن - الإصدار المحسن")
        print(f"   • تاريخ الحجز المطلوب: {target_date}")
        print(f"   • عدد الزبائن: {len(self.clients)}")
        print(f"   • عدد البروكسيات: {len(proxies)}")
        print(f"   • إعداد الجدولة: {self.config.AUTO_LAUNCH_ENABLED}")
        if self.config.AUTO_LAUNCH_ENABLED:
            print(f"   • وقت التحضير: {self.config.PREPARE_LAUNCH_TIME}")
            print(f"   • وقت الحجز: {self.config.BOOKING_LAUNCH_TIME}")
        print("═" * 60)
        print()
        
        # حساب أوقات الجدولة
        prepare_target_ms = 0
        booking_target_ms = 0
        
        if self.config.AUTO_LAUNCH_ENABLED:
            prepare_target_ms = self.scheduler.get_target_timestamp(self.config.PREPARE_LAUNCH_TIME)
            booking_target_ms = self.scheduler.get_target_timestamp(self.config.BOOKING_LAUNCH_TIME)
            
            wait_sec = (prepare_target_ms - int(time.time() * 1000)) / 1000.0
            
            if wait_sec > 0:
                print(f"⏰ وقت التحضير المجدول: {self.scheduler.format_local_time(prepare_target_ms)}")
                print(f"⏳ متبقي {wait_sec:.1f} ثانية...")
                self.scheduler.precise_wait_until(prepare_target_ms)
                print("🚀 بدء عملية التحضير!")
            else:
                print("⚠️ الوقت المحدد قد فات، بدء التشغيل الفوري")
        
        # ── الجولة الأولى ─────────────────────────────────
        print("\n🚀 [الجولة 1] بدء الحجز المتوازي...")
        
        self.run_round(
            clients=self.clients,
            proxies=proxies,
            slots_map=slots_map,
            target_date=target_date,
            prepare_target_ms=prepare_target_ms,
            booking_target_ms=booking_target_ms,
            round_num=1
        )
        
        # إحصاءات الجولة الأولى
        success_r1 = sum(1 for r in self.results.values() if r.get("success", False))
        failed_r1 = len(self.results) - success_r1
        print(f"\n📊 [الجولة 1] ✅ نجح {success_r1} | ❌ فشل {failed_r1}")
        
        # ── الجولة الثانية (إعادة المحاولة) ──────────────
        if self.config.RETRY_ENABLED and failed_r1 > 0 and self.config.MAX_RETRY_ROUNDS > 1:
            failed_clients = self.get_failed_clients()
            
            print(f"\n🔄 [الجولة 2] إعادة المحاولة لـ {len(failed_clients)} زبون فاشل...")
            time.sleep(self.config.RETRY_DELAY_SECONDS)
            
            booking_target_ms2 = booking_target_ms + 5000
            
            self.run_round(
                clients=failed_clients,
                proxies=proxies,
                slots_map=slots_map,
                target_date=target_date,
                prepare_target_ms=prepare_target_ms + 6000,
                booking_target_ms=booking_target_ms2,
                round_num=2
            )
            
            success_r2 = sum(1 for r in self.results.values() 
                           if r.get("success", False) and r.get("round", 1) == 2)
            print(f"\n📊 [الجولة 2] ✅ نجح {success_r2} من أصل {len(failed_clients)}")
        
        # ── إرسال الإيميلات ──────────────────────────────
        if self.config.SEND_EMAILS:
            email_stats = self.email_sender.send_bulk_emails(
                results=self.results,
                clients=self.clients
            )
            
            print(f"\n📧 نتائج إرسال الإيميلات:")
            print(f"   📨 تم إرسال: {email_stats['emails_sent']} إيميل")
            print(f"   ❌ فشل إرسال: {email_stats['emails_failed']} إيميل")
            print(f"   📭 لا يوجد إيميل: {email_stats['no_email']} عميل")
            
            # إرسال إيميل تلخيصي للمشرف
            if self.config.SEND_SUMMARY_EMAIL:
                self.email_sender.send_summary_email(
                    results=self.results,
                    stats=email_stats,
                    clients=self.clients
                )
        
        # ── حفظ النتائج ──────────────────────────────────
        results_list = list(self.results.values())
        
        os.makedirs(self.config.RESULTS_DIR, exist_ok=True)
        
        txt_path = os.path.join(self.config.RESULTS_DIR, "booking_results.txt")
        self.db_handler.save_results(results_list, txt_path)
        
        json_path = os.path.join(self.config.RESULTS_DIR, "booking_results.json")
        self.db_handler.save_results_json(results_list, json_path)
        
        # الإحصاء النهائي
        total_success = sum(1 for r in results_list if r.get("success", False))
        total_failed = len(results_list) - total_success
        
        print("\n" + "═" * 60)
        print(f"🏁 انتهت كافة المحاولات")
        print(f"   ✅ نجح: {total_success} زبون")
        print(f"   ❌ فشل: {total_failed} زبون")
        print(f"   📁 تم حفظ النتائج في: {self.config.RESULTS_DIR}/")
        print("═" * 60)

def run_with_clients(clients: List[Dict], target_date: str = None) -> Dict:
    """تشغيل النظام مع قائمة عملاء محددة (للواجهة)"""
    system = BookingSystem()
    system.clients = clients
    system.run(target_date)
    return system.results

def main():
    """الدالة الرئيسية"""
    target_date = None
    
    if len(sys.argv) >= 2:
        target_date = sys.argv[1]
    
    system = BookingSystem()
    system.run(target_date)

if __name__ == "__main__":
    main()