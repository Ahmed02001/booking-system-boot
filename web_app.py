# web_app.py - النسخة المعدلة بالكامل
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import threading
from datetime import datetime
import sys

# إضافة المجلد الحالي إلى المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import BookingSystem
from database_handler import DatabaseHandler
from email_sender import EmailSender
from config import Config

# إنشاء تطبيق Flask
app = Flask(__name__,
            static_folder=Config.resolve_path('static'),
            template_folder=Config.resolve_path('templates'))
CORS(app)

# تهيئة المكونات
booking_system = BookingSystem()
db_handler = DatabaseHandler()
email_sender = EmailSender()

# تخزين حالة التشغيل
booking_status = {
    "is_running": False,
    "progress": 0,
    "results": {},
    "logs": [],
    "total_clients": 0,
    "completed": 0,
    "emails_sent": 0
}

# ============= الصفحات الرئيسية =============

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/clients')
def clients_page():
    """صفحة إدارة العملاء"""
    return render_template('clients.html')

@app.route('/booking')
def booking_page():
    """صفحة الحجز"""
    return render_template('booking.html')

@app.route('/results')
def results_page():
    """صفحة النتائج"""
    return render_template('results.html')

# ============= الملفات الثابتة =============

@app.route('/static/<path:path>')
def serve_static(path):
    """تقديم الملفات الثابتة"""
    return send_from_directory('static', path)

# ============= APIs =============

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """الحصول على قائمة العملاء"""
    try:
        clients = db_handler.load_clients(Config.resolve_path(Config.DATABASE_PATH))
        
        return jsonify({
            "success": True,
            "data": clients,
            "total": len(clients)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/clients', methods=['POST'])
def add_client():
    """إضافة عميل جديد"""
    try:
        payload = request.get_json(silent=True) or {}
        if not payload.get("id_number") or not payload.get("service_id"):
            return jsonify({"success": False, "error": "رقم الهوية ورقم الخدمة مطلوبان"})

        client = {
            "id_number": str(payload.get("id_number")),
            "service_id": str(payload.get("service_id")),
            "email": payload.get("email", ""),
            "name": payload.get("name", payload.get("id_number", "")),
            "parsed_header": payload.get("parsed_header") or {
                "cookie": payload.get("cookie", ""),
                "user-agent": "Mozilla/5.0",
                "accept-language": "ar"
            }
        }

        db_path = Config.resolve_path(Config.DATABASE_PATH)
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                clients = json.load(f)
        else:
            clients = []

        clients.append(client)

        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(clients, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "message": "تم إضافة العميل بنجاح"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/clients/<id_number>', methods=['DELETE'])
def delete_client(id_number):
    """حذف عميل"""
    try:
        db_path = Config.resolve_path(Config.DATABASE_PATH)
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                clients = json.load(f)
        else:
            clients = []

        clients = [c for c in clients if str(c.get("id_number")) != str(id_number)]

        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(clients, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "success": True,
            "message": "تم حذف العميل بنجاح"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/booking/start', methods=['POST'])
def start_booking():
    """بدء عملية الحجز"""
    global booking_status
    
    if booking_status["is_running"]:
        return jsonify({
            "success": False,
            "error": "عملية حجز قيد التنفيذ بالفعل"
        })
    
    try:
        data = request.get_json(silent=True) or {}
        target_date = data.get('date') or datetime.now().strftime("%Y-%m-%d")
        auto_launch = bool(data.get('auto_launch', True))
        retry_enabled = bool(data.get('retry_enabled', True))
        max_workers = int(data.get('max_workers', 50))
        send_emails = bool(data.get('send_emails', True))

        clients = db_handler.load_clients(Config.resolve_path(Config.DATABASE_PATH))
        
        if not clients:
            return jsonify({
                "success": False,
                "error": "لا يوجد عملاء للحجز"
            })
        
        # تحديث الإعدادات
        booking_system.config.AUTO_LAUNCH_ENABLED = auto_launch
        booking_system.config.RETRY_ENABLED = retry_enabled
        booking_system.config.MAX_WORKERS = min(max_workers, 100)
        booking_system.config.SEND_EMAILS = send_emails
        
        # تحديث الحالة
        booking_status["is_running"] = True
        booking_status["progress"] = 0
        booking_status["results"] = {}
        booking_status["logs"] = []
        booking_status["total_clients"] = len(clients)
        booking_status["completed"] = 0
        booking_status["emails_sent"] = 0
        booking_status["results"] = {}
        
        add_log(f"🚀 بدء عملية الحجز لتاريخ {target_date}")
        add_log(f"👥 عدد العملاء: {len(clients)}")
        
        # تشغيل في خيط منفصل
        thread = threading.Thread(
            target=run_booking_thread,
            args=(clients, target_date)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "بدأت عملية الحجز",
            "total_clients": len(clients)
        })
        
    except Exception as e:
        booking_status["is_running"] = False
        add_log(f"❌ خطأ في بدء الحجز: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/booking/stop', methods=['POST'])
def stop_booking():
    """إيقاف عملية الحجز"""
    global booking_status
    booking_status["is_running"] = False
    add_log("⏹️ تم إيقاف عملية الحجز")
    return jsonify({"success": True})

@app.route('/api/booking/status', methods=['GET'])
def get_booking_status():
    """الحصول على حالة الحجز"""
    global booking_status
    return jsonify({
        "is_running": booking_status["is_running"],
        "progress": booking_status["progress"],
        "total_clients": booking_status["total_clients"],
        "completed": booking_status["completed"],
        "emails_sent": booking_status["emails_sent"],
        "logs": booking_status["logs"][-50:],
        "results": booking_status["results"]
    })

@app.route('/api/booking/results', methods=['GET'])
def get_results():
    """الحصول على النتائج النهائية"""
    try:
        results_path = Config.resolve_path(os.path.join(Config.RESULTS_DIR, "booking_results.json"))
        if os.path.exists(results_path):
            with open(results_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            return jsonify({"success": True, "data": results})
        return jsonify({"success": False, "error": "لا توجد نتائج"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """الحصول على سجل العمليات"""
    return jsonify({"logs": booking_status["logs"][-100:]})

# ============= وظائف مساعدة =============

def add_log(message):
    """إضافة رسالة للسجل"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    booking_status["logs"].append(log_entry)
    print(log_entry)

def run_booking_thread(clients, target_date):
    """تشغيل الحجز في خيط منفصل"""
    global booking_status
    
    try:
        # تشغيل النظام
        booking_system.clients = clients
        
        # تعطيل إرسال الإيميلات في الخلفية مؤقتاً لتجنب التعقيد
        original_send_emails = booking_system.config.SEND_EMAILS
        booking_system.config.SEND_EMAILS = False
        
        booking_system.run(target_date)
        
        # استعادة الإعدادات
        booking_system.config.SEND_EMAILS = original_send_emails
        
        # تحديث النتائج
        booking_status["results"] = booking_system.results
        
        # حساب الإحصائيات
        success = sum(1 for r in booking_status["results"].values() if r.get("success", False))
        failed = len(booking_status["results"]) - success
        
        add_log(f"🏁 انتهت عملية الحجز")
        add_log(f"✅ نجح: {success} | ❌ فشل: {failed}")
        
        booking_status["progress"] = 100
        booking_status["completed"] = booking_status["total_clients"]
        
    except Exception as e:
        add_log(f"❌ خطأ في الحجز: {str(e)}")
    
    finally:
        booking_status["is_running"] = False

# ============= تشغيل السيرفر =============

if __name__ == "__main__":
    # إنشاء المجلدات إذا لم تكن موجودة
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    
    print("=" * 60)
    print("🌐 تشغيل خادم الويب - نظام الحجز التلقائي")
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("📍 افتح المتصفح على: http://localhost:5000")
    print("=" * 60)
    print("\n⚠️ تأكد من وجود الملفات التالية:")
    print("   - templates/index.html")
    print("   - templates/clients.html")
    print("   - templates/booking.html")
    print("   - templates/results.html")
    print("   - static/css/style.css")
    print("   - static/js/script.js")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)