# web_app.py - أبسط نسخة تعمل 100% على Railway
from flask import Flask
import os

# إنشاء التطبيق
app = Flask(__name__)

# المسار الرئيسي
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>نظام الحجز</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; direction: rtl; }
            .success { color: green; font-size: 24px; }
            .info { background: #f0f0f0; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 500px; }
        </style>
    </head>
    <body>
        <h1>✅ نظام الحجز التلقائي</h1>
        <p class="success">🚀 التطبيق يعمل بنجاح على Railway!</p>
        <div class="info">
            <p><strong>الوقت:</strong> <span id="time"></span></p>
            <p><strong>الحالة:</strong> Online ✅</p>
        </div>
        <p>📌 جرب: <a href="/api/health">/api/health</a></p>
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString('ar-EG');
        </script>
    </body>
    </html>
    """

# API للتحقق من الصحة
@app.route('/api/health')
def health():
    return {"status": "healthy", "message": "Booking system is running!"}

# API بسيط
@app.route('/api/status')
def status():
    return {"status": "online", "timestamp": str(__import__('datetime').datetime.now())}

# تشغيل التطبيق (للاستخدام المحلي فقط)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)