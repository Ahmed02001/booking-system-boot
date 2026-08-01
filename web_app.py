# web_app.py - نسخة كاملة لـ Railway
import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# ===== إعدادات البيئة =====
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# ===== إنشاء المجلدات =====
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('results', exist_ok=True)

# ===== إنشاء تطبيق Flask =====
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# ===== مساعدات =====
def add_log(message):
    """إضافة رسالة للسجل"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# ===== الصفحات =====
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except:
        return "<h1>نظام الحجز التلقائي</h1><p>مرحباً بك في النظام</p>"

@app.route('/clients')
def clients_page():
    try:
        return render_template('clients.html')
    except:
        return "<h1>إدارة العملاء</h1>"

@app.route('/booking')
def booking_page():
    try:
        return render_template('booking.html')
    except:
        return "<h1>صفحة الحجز</h1>"

@app.route('/results')
def results_page():
    try:
        return render_template('results.html')
    except:
        return "<h1>النتائج</h1>"

# ===== APIs =====

def load_clients_data():
    if os.path.exists("database_backup.json"):
        with open("database_backup.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_clients_data(clients):
    with open("database_backup.json", 'w', encoding='utf-8') as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)


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
            "parsed_header": data.get("parsed_header", {}),
            "status": "pending"
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
        "total_clients": 0,
        "completed": 0,
        "logs": ["✅ النظام يعمل على Railway"],
        "results": {}
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": ["✅ النظام يعمل على Railway"]})

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
    """فحص صحة التطبيق"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get('RAILWAY_ENVIRONMENT', 'development')
    })

@app.route('/api/env', methods=['GET'])
def check_env():
    """التحقق من متغيرات البيئة"""
    safe_vars = {
        'API_KEY': os.environ.get('API_KEY', 'Not set')[:20] + '...' if os.environ.get('API_KEY') else 'Not set',
        'BASE_URL': os.environ.get('BASE_URL', 'Not set'),
        'MAX_WORKERS': os.environ.get('MAX_WORKERS', 'Not set'),
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Not set'),
        'PORT': os.environ.get('PORT', 'Not set'),
    }
    return jsonify(safe_vars)

# ===== تشغيل التطبيق =====
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 تشغيل نظام الحجز على Railway")
    print(f"📍 المنفذ: {PORT}")
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=PORT, debug=False)