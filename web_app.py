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
@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        if os.path.exists("database_backup.json"):
            with open("database_backup.json", 'r', encoding='utf-8') as f:
                clients = json.load(f)
        else:
            clients = []
        return jsonify({"success": True, "data": clients, "total": len(clients)})
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
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)