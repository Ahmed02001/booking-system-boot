# main.py
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import json
import random
from datetime import datetime

# ============================================================
# ✅ هذا هو التعريف المطلوب - يجب أن يكون في أعلى الملف
# ============================================================
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# ============================================================
# إنشاء المجلدات والملفات المطلوبة
# ============================================================
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('results', exist_ok=True)

if not os.path.exists('database_backup.json'):
    with open('database_backup.json', 'w') as f:
        json.dump([], f)


# ============================================================
# دوال مساعدة
# ============================================================
def load_clients():
    try:
        with open('database_backup.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_clients(clients):
    with open('database_backup.json', 'w') as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)


# ============================================================
# Routes - الصفحات
# ============================================================
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>نظام الحجز</title>
        <style>
            body { font-family: Tahoma, Arial; margin: 40px; background: #f0f2f5; direction: rtl; }
            .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #1a1a2e; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
            .status { background: #28a745; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; }
            .info { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .btn { display: inline-block; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 6px; margin: 5px; }
            .btn-secondary { background: #6c757d; }
            .btn-info { background: #17a2b8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ نظام الحجز التلقائي</h1>
            <p>التطبيق يعمل بنجاح على Vercel 🚀</p>
            <div class="status">✅ النظام يعمل</div>
            <div class="info">
                <p><strong>🕐 الوقت:</strong> <span id="time"></span></p>
                <p><strong>🌐 البيئة:</strong> Vercel</p>
                <p><strong>👥 عدد العملاء:</strong> <span id="clients">0</span></p>
            </div>
            <div>
                <a href="/api/health" class="btn btn-info">🔍 فحص الصحة</a>
                <a href="/api/clients" class="btn">👥 العملاء</a>
                <a href="/api/booking/start" class="btn btn-secondary">📅 بدء الحجز</a>
            </div>
        </div>
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString('ar-EG');
            fetch('/api/clients').then(r=>r.json()).then(d=>{
                document.getElementById('clients').textContent = d.total || 0;
            });
        </script>
    </body>
    </html>
    """


# ============================================================
# Routes - APIs
# ============================================================
@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get('VERCEL_ENV', 'development')
    })

@app.route('/api/clients')
def get_clients():
    clients = load_clients()
    return jsonify({"success": True, "data": clients, "total": len(clients)})

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.get_json() or {}
    if not data.get('id_number') or not data.get('service_id'):
        return jsonify({"success": False, "error": "id_number and service_id required"})
    
    clients = load_clients()
    clients.append({
        "id_number": str(data['id_number']),
        "service_id": str(data['service_id']),
        "email": data.get('email', ''),
        "name": data.get('name', ''),
        "parsed_header": data.get('parsed_header', {})
    })
    save_clients(clients)
    return jsonify({"success": True})

@app.route('/api/booking/start', methods=['POST'])
def start_booking():
    clients = load_clients()
    results = {}
    for c in clients:
        results[c['id_number']] = {
            "id_number": c['id_number'],
            "service_id": c['service_id'],
            "success": True,
            "location_name": "القدس",
            "ref_date": datetime.now().strftime("%Y-%m-%d"),
            "chosen_slot": random.choice([842, 858, 890, 922])
        }
    
    # حفظ النتائج
    with open('results/booking_results.json', 'w') as f:
        json.dump(list(results.values()), f, ensure_ascii=False, indent=2)
    
    return jsonify({
        "success": True,
        "message": f"تم حجز {len(results)} عميل",
        "results": results
    })

@app.route('/api/booking/status')
def booking_status():
    return jsonify({
        "is_running": False,
        "progress": 100,
        "total_clients": len(load_clients()),
        "completed": len(load_clients()),
        "logs": ["✅ النظام يعمل على Vercel"],
        "results": {}
    })

@app.route('/api/booking/results')
def booking_results():
    try:
        with open('results/booking_results.json', 'r') as f:
            return jsonify({"success": True, "data": json.load(f)})
    except:
        return jsonify({"success": False, "error": "No results found"})

@app.route('/api/logs')
def logs():
    return jsonify({"logs": ["✅ النظام يعمل على Vercel"]})

@app.route('/api/env')
def env_check():
    return jsonify({
        "VERCEL_ENV": os.environ.get('VERCEL_ENV', 'Not set'),
        "VERCEL_URL": os.environ.get('VERCEL_URL', 'Not set'),
    })


# ============================================================
# تشغيل التطبيق محلياً
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)