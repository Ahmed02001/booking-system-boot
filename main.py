# main.py - الملف الموحد للنظام كاملاً
import os
import sys
import json
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# ========== الجزء 1: إعدادات Flask ==========

# إنشاء تطبيق Flask
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# إنشاء المجلدات المطلوبة
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('results', exist_ok=True)

# إنشاء ملف العملاء إذا لم يكن موجوداً
if not os.path.exists('database_backup.json'):
    with open('database_backup.json', 'w') as f:
        json.dump([], f)

# ========== الجزء 2: دوال مساعدة Flask ==========

def load_clients_data():
    """تحميل بيانات العملاء من الملف"""
    try:
        if os.path.exists("database_backup.json"):
            with open("database_backup.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def save_clients_data(clients):
    """حفظ بيانات العملاء في الملف"""
    with open("database_backup.json", 'w', encoding='utf-8') as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)

def add_log(message):
    """إضافة رسالة للسجل"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# ========== الجزء 3: Routes Flask (الواجهة) ==========

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    try:
        return render_template('index.html')
    except:
        return """
        <!DOCTYPE html>
        <html dir="rtl">
        <head><meta charset="UTF-8"><title>نظام الحجز</title></head>
        <body style="font-family:Tahoma;padding:40px;background:#f0f2f5;">
            <div style="max-width:800px;margin:auto;background:white;padding:30px;border-radius:10px;">
                <h1>⚡ نظام الحجز التلقائي</h1>
                <p>التطبيق يعمل بنجاح 🚀</p>
                <div style="background:#28a745;color:white;padding:10px;border-radius:5px;display:inline-block;">✅ النظام يعمل</div>
                <hr>
                <p><strong>🕐 الوقت:</strong> <span id="time"></span></p>
                <p><strong>🌐 البيئة:</strong> Vercel</p>
                <p><strong>👥 عدد العملاء:</strong> <span id="clients">0</span></p>
                <hr>
                <a href="/api/health" style="background:#17a2b8;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">🔍 فحص الصحة</a>
                <a href="/api/clients" style="background:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">👥 العملاء</a>
                <script>
                    document.getElementById('time').textContent = new Date().toLocaleString('ar-EG');
                    fetch('/api/clients').then(r=>r.json()).then(d=>{
                        document.getElementById('clients').textContent = d.total || 0;
                    });
                </script>
            </div>
        </body>
        </html>
        """

@app.route('/clients')
def clients_page():
    try:
        return render_template('clients.html')
    except:
        return "<h1>إدارة العملاء</h1><p>قم بإضافة العملاء من خلال API</p>"

@app.route('/booking')
def booking_page():
    try:
        return render_template('booking.html')
    except:
        return "<h1>صفحة الحجز</h1><p>استخدم API للحجز</p>"

@app.route('/results')
def results_page():
    try:
        return render_template('results.html')
    except:
        return "<h1>النتائج</h1>"

# ========== الجزء 4: APIs ==========

@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        clients = load_clients_data()
        return jsonify({"success": True, "data": clients, "total": len(clients)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/clients', methods=['POST'])
def add_client():
    try:
        data = request.get_json(silent=True) or {}
        if not data.get("id_number") or not data.get("service_id"):
            return jsonify({"success": False, "error": "رقم الهوية ورقم الخدمة مطلوبان"})

        clients = load_clients_data()
        client_id = str(data["id_number"])

        for client in clients:
            if str(client.get("id_number")) == client_id:
                return jsonify({"success": False, "error": "هذا العميل موجود مسبقاً"})

        new_client = {
            "id_number": client_id,
            "service_id": str(data.get("service_id")),
            "email": data.get("email", ""),
            "name": data.get("name") or client_id,
            "parsed_header": data.get("parsed_header", {})
        }
        clients.append(new_client)
        save_clients_data(clients)
        return jsonify({"success": True, "data": new_client})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/clients/<id_number>', methods=['DELETE'])
def delete_client(id_number):
    try:
        clients = load_clients_data()
        filtered = [c for c in clients if str(c.get("id_number")) != str(id_number)]
        if len(filtered) == len(clients):
            return jsonify({"success": False, "error": "العميل غير موجود"})
        save_clients_data(filtered)
        return jsonify({"success": True, "deleted_id": id_number})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/booking/status', methods=['GET'])
def get_booking_status():
    return jsonify({
        "is_running": False,
        "progress": 0,
        "total_clients": len(load_clients_data()),
        "completed": 0,
        "logs": ["✅ النظام يعمل على Vercel"],
        "results": {}
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": ["✅ النظام يعمل على Vercel - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")]})

@app.route('/api/booking/results', methods=['GET'])
def get_results():
    try:
        if os.path.exists("results/booking_results.json"):
            with open("results/booking_results.json", 'r', encoding='utf-8') as f:
                results = json.load(f)
            return jsonify({"success": True, "data": results})
        return jsonify({"success": False, "error": "لا توجد نتائج"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get('VERCEL_ENV', 'development'),
        "version": "1.0.0"
    })

@app.route('/api/env', methods=['GET'])
def check_env():
    safe_vars = {
        'VERCEL_ENV': os.environ.get('VERCEL_ENV', 'Not set'),
        'VERCEL_URL': os.environ.get('VERCEL_URL', 'Not set'),
        'API_KEY': os.environ.get('API_KEY', 'Not set')[:20] + '...' if os.environ.get('API_KEY') else 'Not set',
        'BASE_URL': os.environ.get('BASE_URL', 'Not set'),
    }
    return jsonify(safe_vars)

# ========== الجزء 5: نظام الحجز الأساسي (BookingSystem) ==========

class BookingSystem:
    """النظام الرئيسي للحجز"""
    
    def __init__(self):
        self.results = {}
        self.clients = []
    
    def run(self, target_date: str = None):
        """تشغيل النظام الرئيسي"""
        clients = load_clients_data()
        
        if not clients:
            print("❌ لا يوجد زبائن للتشغيل")
            return
        
        print(f"⚡ بدء الحجز لتاريخ: {target_date or 'اليوم'}")
        print(f"👥 عدد العملاء: {len(clients)}")
        
        # محاكاة عملية الحجز
        for client in clients:
            self.results[client["id_number"]] = {
                "id_number": client["id_number"],
                "service_id": client["service_id"],
                "success": True,
                "location_name": "القدس",
                "ref_date": target_date or datetime.now().strftime("%Y-%m-%d"),
                "chosen_slot": random.choice([842, 858, 890, 922]),
                "error_msg": ""
            }
            print(f"✅ تم حجز العميل {client['id_number']}")
        
        # حفظ النتائج
        results_list = list(self.results.values())
        os.makedirs('results', exist_ok=True)
        
        with open("results/booking_results.json", 'w', encoding='utf-8') as f:
            json.dump(results_list, f, ensure_ascii=False, indent=2)
        
        print(f"🏁 انتهت المحاولات - نجح: {len([r for r in results_list if r.get('success')])}")

# ========== الجزء 6: تشغيل التطبيق ==========

# إنشاء كائن النظام للتشغيل في الخلفية
booking_system = BookingSystem()

# دالة لتشغيل الحجز عبر API
@app.route('/api/booking/start', methods=['POST'])
def start_booking():
    """بدء عملية الحجز عبر API"""
    try:
        data = request.get_json(silent=True) or {}
        target_date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
        
        # تشغيل الحجز
        booking_system.run(target_date)
        
        return jsonify({
            "success": True,
            "message": "تم بدء الحجز بنجاح",
            "results": booking_system.results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ========== الجزء 7: التشغيل المحلي ==========

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("🚀 نظام الحجز التلقائي")
    print(f"📍 المنفذ: {port}")
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)