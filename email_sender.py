# email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
import time
from typing import List, Dict
from datetime import datetime
import logging

class EmailSender:
    """نظام إرسال الإيميلات للعملاء"""
    
    def __init__(self, config_file="email_config.json"):
        self.config = self.load_config(config_file)
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
    
    def setup_logging(self):
        """إعداد نظام التسجيل"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self, config_file):
        """تحميل إعدادات الإيميل من ملف"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # إعدادات افتراضية
            return {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your_email@gmail.com",
                "sender_password": "your_app_password",
                "use_tls": True,
                "admin_email": "admin@example.com",
                "email_subject_prefix": "[MyVisit] ",
                "email_delay_seconds": 1
            }
    
    def send_booking_email(self, client_data: Dict, booking_result: Dict) -> bool:
        """إرسال إيميل تأكيد حجز لعميل واحد"""
        try:
            # استخراج البيانات
            client_id = client_data.get("id_number", "غير معروف")
            service_id = client_data.get("service_id", "غير معروف")
            location = booking_result.get("location_name", "غير معروف")
            ref_date = booking_result.get("ref_date", "غير معروف")
            slot = booking_result.get("chosen_slot", 0)
            client_name = client_data.get("name", client_id)
            
            # الحصول على إيميل العميل
            client_email = self.extract_email_from_data(client_data)
            
            if not client_email:
                self.logger.warning(f"⚠️ لا يوجد إيميل للعميل {client_id}")
                return False
            
            # بناء محتوى الإيميل
            subject = f"{self.config.get('email_subject_prefix', '')}✅ تأكيد حجز الموعد - الخدمة {service_id}"
            
            # الإيميل بتنسيق HTML
            html_body = self.build_html_email(
                client_name=client_name,
                client_id=client_id,
                service_id=service_id,
                location=location,
                ref_date=ref_date,
                slot=slot
            )
            
            # الإيميل بتنسيق نص عادي (للأجهزة التي لا تدعم HTML)
            text_body = self.build_text_email(
                client_name=client_name,
                client_id=client_id,
                service_id=service_id,
                location=location,
                ref_date=ref_date,
                slot=slot
            )
            
            # إرسال الإيميل
            success = self.send_email(
                to_email=client_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            if success:
                self.logger.info(f"✅ تم إرسال إيميل للعميل {client_id} -> {client_email}")
            else:
                self.logger.error(f"❌ فشل إرسال إيميل للعميل {client_id}")
            
            # تأخير بين الإيميلات لتجنب الحظر
            time.sleep(self.config.get("email_delay_seconds", 1))
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إرسال الإيميل: {e}")
            return False
    
    def build_html_email(self, client_name: str, client_id: str, service_id: str,
                         location: str, ref_date: str, slot: int) -> str:
        """بناء قالب الإيميل بتنسيق HTML"""
        slot_time = self.convert_slot_to_time(slot)
        
        return f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Tahoma', 'Arial', sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 25px; text-align: center; }}
                .header h2 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .greeting {{ font-size: 18px; margin-bottom: 20px; }}
                .details {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-right: 4px solid #4CAF50; }}
                .details-item {{ padding: 8px 0; border-bottom: 1px solid #e9ecef; }}
                .details-item:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #495057; }}
                .value {{ color: #212529; }}
                .notes {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-right: 4px solid #ffc107; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; color: #6c757d; font-size: 12px; border-top: 1px solid #dee2e6; }}
                .highlight {{ color: #4CAF50; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✅ تأكيد حجز الموعد</h2>
                    <p style="margin: 5px 0 0; opacity: 0.9;">تم تأكيد حجزك بنجاح</p>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        مرحباً <strong>{client_name}</strong>،
                    </div>
                    
                    <p>يسعدنا إعلامك بأنه تم تأكيد حجز الموعد الخاص بك بنجاح ✅</p>
                    
                    <div class="details">
                        <h4 style="margin-top: 0; color: #4CAF50;">📋 تفاصيل الحجز:</h4>
                        <div class="details-item">
                            <span class="label">🆔 رقم العميل:</span>
                            <span class="value">{client_id}</span>
                        </div>
                        <div class="details-item">
                            <span class="label">🏢 رقم الخدمة:</span>
                            <span class="value">{service_id}</span>
                        </div>
                        <div class="details-item">
                            <span class="label">📍 الموقع:</span>
                            <span class="value">{location}</span>
                        </div>
                        <div class="details-item">
                            <span class="label">📆 تاريخ الموعد:</span>
                            <span class="value">{ref_date}</span>
                        </div>
                        <div class="details-item">
                            <span class="label">⏰ وقت الموعد:</span>
                            <span class="value highlight">{slot_time}</span>
                        </div>
                    </div>
                    
                    <div class="notes">
                        <h4 style="margin-top: 0; color: #856404;">📝 ملاحظات هامة:</h4>
                        <ul style="margin: 5px 0; padding-right: 20px;">
                            <li>⏰ يرجى الوصول قبل الموعد بـ <strong>15 دقيقة</strong></li>
                            <li>🪪 أحضر معك <strong>بطاقة الهوية</strong> أو جواز السفر</li>
                            <li>📱 في حال التأخير، يرجى الاتصال على الرقم المخصص</li>
                            <li>💳 تأكد من إحضار وسيلة الدفع إذا كانت مطلوبة</li>
                        </ul>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; text-align: center; margin-top: 20px;">
                        شكراً لاستخدامك خدماتنا 🙏
                    </p>
                </div>
                
                <div class="footer">
                    <small>هذا البريد إلكتروني آلي، يرجى عدم الرد عليه.</small><br>
                    <small>© {datetime.now().year} جميع الحقوق محفوظة</small>
                </div>
            </div>
        </body>
        </html>
        """
    
    def build_text_email(self, client_name: str, client_id: str, service_id: str,
                         location: str, ref_date: str, slot: int) -> str:
        """بناء الإيميل بتنسيق نص عادي"""
        slot_time = self.convert_slot_to_time(slot)
        
        return f"""
        ✅ تأكيد حجز الموعد
        
        مرحباً {client_name}،
        
        تم تأكيد حجز الموعد الخاص بك بنجاح ✅
        
        📋 تفاصيل الحجز:
        ─────────────────
        🆔 رقم العميل: {client_id}
        🏢 رقم الخدمة: {service_id}
        📍 الموقع: {location}
        📆 تاريخ الموعد: {ref_date}
        ⏰ وقت الموعد: {slot_time}
        
        📝 ملاحظات هامة:
        ─────────────────
        • يرجى الوصول قبل الموعد بـ 15 دقيقة
        • أحضر معك بطاقة الهوية
        • في حال التأخير، يرجى الاتصال على الرقم المخصص
        
        شكراً لاستخدامك خدماتنا 🙏
        
        هذا البريد إلكتروني آلي، يرجى عدم الرد عليه.
        """
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """إرسال إيميل واحد بتنسيق HTML ونص عادي"""
        try:
            # إنشاء الرسالة
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config["sender_email"]
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # إضافة النص العادي (احتياطي)
            if text_body:
                part1 = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(part1)
            
            # إضافة HTML
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part2)
            
            # الاتصال بالسيرفر
            server = smtplib.SMTP(
                self.config["smtp_server"], 
                self.config["smtp_port"]
            )
            
            if self.config.get("use_tls", True):
                server.starttls()
            
            # تسجيل الدخول
            server.login(
                self.config["sender_email"],
                self.config["sender_password"]
            )
            
            # إرسال الإيميل
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل إرسال الإيميل إلى {to_email}: {e}")
            return False
    
    def send_bulk_emails(self, results: Dict, clients: List[Dict]) -> Dict:
        """إرسال إيميلات لجميع العملاء الذين نجح حجزهم"""
        if not self.config.get("enabled", True):
            return {"emails_sent": 0, "emails_failed": 0, "no_email": 0}
        
        stats = {
            "total_successful": 0,
            "emails_sent": 0,
            "emails_failed": 0,
            "no_email": 0
        }
        
        print("\n📧 جاري إرسال الإيميلات للعملاء الناجحين...")
        
        for client in clients:
            client_id = client.get("id_number")
            result = results.get(client_id, {})
            
            if result.get("success", False):
                stats["total_successful"] += 1
                
                if self.send_booking_email(client, result):
                    stats["emails_sent"] += 1
                else:
                    if not self.extract_email_from_data(client):
                        stats["no_email"] += 1
                    else:
                        stats["emails_failed"] += 1
        
        return stats
    
    def extract_email_from_data(self, client: Dict) -> str:
        """استخراج الإيميل من بيانات العميل"""
        # طريقة 1: من حقل email مباشر
        if "email" in client and client["email"]:
            return client["email"]
        
        # طريقة 2: من الـ headers (كوكيز)
        headers = client.get("headers", {})
        cookie = headers.get("cookie", "")
        
        # محاولة استخراج الإيميل من الكوكيز
        if "email=" in cookie:
            start = cookie.find("email=") + 6
            end = cookie.find(";", start)
            if end == -1:
                end = len(cookie)
            email = cookie[start:end]
            if "@" in email:
                return email
        
        # طريقة 3: من بيانات إضافية
        if "parsed_header" in client:
            extra = client["parsed_header"]
            if "email" in extra:
                return extra["email"]
        
        return None
    
    def convert_slot_to_time(self, slot: int) -> str:
        """تحويل رقم الساعة إلى وقت readable"""
        hours = slot // 60
        minutes = slot % 60
        return f"{hours:02d}:{minutes:02d}"
    
    def send_summary_email(self, results: Dict, stats: Dict, clients: List[Dict]) -> bool:
        """إرسال إيميل تلخيصي للمشرف"""
        admin_email = self.config.get("admin_email")
        if not admin_email:
            return False
        
        total = len(results)
        success = sum(1 for r in results.values() if r.get("success", False))
        failed = total - success
        
        subject = "📊 تقرير عملية الحجز - " + datetime.now().strftime("%Y-%m-%d %H:%M")
        
        html_body = f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: Tahoma, Arial; padding: 20px; }}
                .container {{ max-width: 800px; margin: auto; background: #f8f9fa; padding: 20px; border-radius: 10px; }}
                .header {{ background: #007bff; color: white; padding: 15px; border-radius: 8px; text-align: center; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ background: white; padding: 15px; border-radius: 8px; text-align: center; flex: 1; margin: 0 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .stat-number {{ font-size: 28px; font-weight: bold; color: #007bff; }}
                .stat-label {{ color: #6c757d; }}
                .success {{ color: #28a745; }}
                .failed {{ color: #dc3545; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: right; border-bottom: 1px solid #dee2e6; }}
                th {{ background: #e9ecef; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 تقرير عملية الحجز</h2>
                    <p>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">{total}</div>
                        <div class="stat-label">👥 إجمالي العملاء</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number success">{success}</div>
                        <div class="stat-label">✅ نجح</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number failed">{failed}</div>
                        <div class="stat-label">❌ فشل</div>
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">{stats.get('emails_sent', 0)}</div>
                        <div class="stat-label">📨 إيميلات مرسلة</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{stats.get('emails_failed', 0)}</div>
                        <div class="stat-label">❌ فشل الإرسال</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{stats.get('no_email', 0)}</div>
                        <div class="stat-label">📭 لا يوجد إيميل</div>
                    </div>
                </div>
                
                <h3>📋 تفاصيل العملاء الناجحين</h3>
                <table>
                    <thead>
                        <tr>
                            <th>رقم العميل</th>
                            <th>الخدمة</th>
                            <th>الموقع</th>
                            <th>التاريخ</th>
                            <th>الوقت</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for client in clients:
            client_id = client.get("id_number")
            result = results.get(client_id, {})
            if result.get("success", False):
                html_body += f"""
                        <tr>
                            <td>{client_id}</td>
                            <td>{result.get('service_id', 'N/A')}</td>
                            <td>{result.get('location_name', 'N/A')}</td>
                            <td>{result.get('ref_date', 'N/A')}</td>
                            <td>{self.convert_slot_to_time(result.get('chosen_slot', 0))}</td>
                        </tr>
                """
        
        html_body += """
                    </tbody>
                </table>
                
                <div class="footer">
                    <small>تم الإرسال بواسطة نظام الحجز التلقائي</small>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        📊 تقرير عملية الحجز
        ====================
        
        📅 التاريخ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        👥 إجمالي العملاء: {total}
        ✅ نجح: {success}
        ❌ فشل: {failed}
        
        📧 تفاصيل الإيميلات:
        📨 تم إرسال: {stats.get('emails_sent', 0)}
        ❌ فشل الإرسال: {stats.get('emails_failed', 0)}
        📭 لا يوجد إيميل: {stats.get('no_email', 0)}
        
        تم الإرسال بواسطة نظام الحجز التلقائي
        """
        
        return self.send_email(admin_email, subject, html_body, text_body)