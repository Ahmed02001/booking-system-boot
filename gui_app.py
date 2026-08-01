# gui_app.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
import time
from datetime import datetime
import os

from main import BookingSystem, run_with_clients
from database_handler import DatabaseHandler
from email_sender import EmailSender

class BookingGUI:
    """واجهة المستخدم الرسومية لنظام الحجز"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("نظام الحجز التلقائي - MyVisit")
        self.root.geometry("1100x750")
        self.root.configure(bg='#f0f0f0')
        
        self.root.option_add('*Font', 'Tahoma 11')
        
        self.booking_system = BookingSystem()
        self.db_handler = DatabaseHandler()
        self.email_sender = EmailSender()
        self.clients = []
        self.results = {}
        self.is_running = False
        
        self.create_widgets()
        self.load_default_data()
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # ========== الجزء الأيسر: إدارة العملاء ==========
        ttk.Label(left_frame, text="👥 إدارة العملاء", font=('Tahoma', 14, 'bold')).grid(row=0, column=0, columnspan=3, pady=10)
        
        ttk.Button(left_frame, text="📂 تحميل العملاء", command=self.load_clients).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(left_frame, text="➕ إضافة عميل", command=self.add_client_dialog).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(left_frame, text="🗑️ حذف المحدد", command=self.delete_selected).grid(row=1, column=2, padx=5, pady=5)
        
        columns = ('ID', 'الخدمة', 'الإيميل', 'الحالة')
        self.clients_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)
        self.clients_tree.heading('ID', text='رقم الهوية')
        self.clients_tree.heading('الخدمة', text='رقم الخدمة')
        self.clients_tree.heading('الإيميل', text='البريد الإلكتروني')
        self.clients_tree.heading('الحالة', text='الحالة')
        self.clients_tree.column('ID', width=130)
        self.clients_tree.column('الخدمة', width=90)
        self.clients_tree.column('الإيميل', width=150)
        self.clients_tree.column('الحالة', width=100)
        self.clients_tree.grid(row=2, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        scrollbar.grid(row=2, column=3, sticky='ns')
        self.clients_tree.configure(yscrollcommand=scrollbar.set)
        
        self.clients_count_label = ttk.Label(left_frame, text="عدد العملاء: 0")
        self.clients_count_label.grid(row=3, column=0, columnspan=3, pady=5)
        
        # ========== الجزء الأيمن: التحكم ==========
        settings_frame = ttk.LabelFrame(right_frame, text="⚙️ إعدادات الحجز", padding="10")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(settings_frame, text="📅 تاريخ الحجز:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.date_entry = ttk.Entry(settings_frame, width=15)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(settings_frame, text="⚡ عدد الخيوط:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.workers_entry = ttk.Entry(settings_frame, width=15)
        self.workers_entry.grid(row=1, column=1, padx=5, pady=5)
        self.workers_entry.insert(0, "50")
        
        self.retry_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="🔄 إعادة المحاولة", variable=self.retry_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.schedule_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="⏰ جدولة دقيقة", variable=self.schedule_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # ========== إعدادات الإيميل ==========
        email_frame = ttk.LabelFrame(right_frame, text="📧 إعدادات الإيميل", padding="10")
        email_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.send_email_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(email_frame, text="📨 إرسال إيميلات للعملاء", 
                       variable=self.send_email_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.send_summary_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(email_frame, text="📊 إرسال تقرير للمشرف", 
                       variable=self.send_summary_var).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Button(email_frame, text="⚙️ إعدادات الإيميل", 
                  command=self.email_settings_dialog).grid(row=2, column=0, pady=5, sticky=tk.W)
        
        # ========== أزرار التحكم ==========
        control_frame = ttk.Frame(right_frame)
        control_frame.grid(row=2, column=0, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="🚀 بدء الحجز", command=self.start_booking, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ إيقاف", command=self.stop_booking, width=15, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="📊 عرض النتائج", command=self.show_results, width=15).grid(row=0, column=2, padx=5)
        
        # ========== سجل العمليات ==========
        log_frame = ttk.LabelFrame(right_frame, text="📋 سجل العمليات", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # ضبط الأوزان
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        left_frame.columnconfigure(2, weight=1)
        left_frame.rowconfigure(2, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def load_default_data(self):
        """تحميل البيانات الافتراضية"""
        try:
            self.clients = self.db_handler.load_clients("database_backup.json")
            self.update_clients_list()
            self.log("✅ تم تحميل العملاء بنجاح")
        except Exception as e:
            self.log(f"⚠️ لم يتم العثور على ملف العملاء الافتراضي: {e}")
    
    def load_clients(self):
        """تحميل العملاء من ملف"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="اختر ملف العملاء",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.clients = self.db_handler.load_clients(file_path)
                self.update_clients_list()
                self.log(f"✅ تم تحميل {len(self.clients)} عميل من {file_path}")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل تحميل الملف: {e}")
    
    def add_client_dialog(self):
        """إضافة عميل جديد"""
        dialog = tk.Toplevel(self.root)
        dialog.title("إضافة عميل جديد")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="رقم الهوية:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        id_entry = ttk.Entry(dialog, width=30)
        id_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="رقم الخدمة:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        service_entry = ttk.Entry(dialog, width=30)
        service_entry.grid(row=1, column=1, padx=10, pady=10)
        service_entry.insert(0, "4937")
        
        ttk.Label(dialog, text="البريد الإلكتروني:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        email_entry = ttk.Entry(dialog, width=30)
        email_entry.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="الاسم:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=3, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="الكوكيز (Cookie):").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        cookie_text = scrolledtext.ScrolledText(dialog, height=5, width=30)
        cookie_text.grid(row=4, column=1, padx=10, pady=10)
        
        def save_client():
            id_num = id_entry.get().strip()
            service = service_entry.get().strip()
            email = email_entry.get().strip()
            name = name_entry.get().strip()
            cookie = cookie_text.get("1.0", tk.END).strip()
            
            if not id_num or not service or not cookie:
                messagebox.showerror("خطأ", "رقم الهوية ورقم الخدمة والكوكيز مطلوبة")
                return
            
            client = {
                "id_number": id_num,
                "service_id": service,
                "email": email,
                "name": name or id_num,
                "parsed_header": {
                    "cookie": cookie,
                    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15",
                    "accept-language": "ar"
                }
            }
            
            self.clients.append(client)
            self.update_clients_list()
            self.log(f"✅ تم إضافة عميل {id_num}")
            dialog.destroy()
        
        ttk.Button(dialog, text="💾 حفظ", command=save_client).grid(row=5, column=0, columnspan=2, pady=20)
    
    def delete_selected(self):
        """حذف العميل المحدد"""
        selected = self.clients_tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "الرجاء تحديد عميل للحذف")
            return
        
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف العميل المحدد؟"):
            for item in selected:
                values = self.clients_tree.item(item, 'values')
                id_num = values[0]
                self.clients = [c for c in self.clients if c.get("id_number") != id_num]
            self.update_clients_list()
            self.log(f"🗑️ تم حذف {len(selected)} عميل")
    
    def update_clients_list(self):
        """تحديث قائمة العملاء"""
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        
        for client in self.clients:
            id_num = client.get("id_number", "غير معروف")
            service = client.get("service_id", "غير معروف")
            email = client.get("email", "غير مسجل")
            status = self.results.get(id_num, {}).get("status", "⏳ في الانتظار")
            self.clients_tree.insert('', 'end', values=(id_num, service, email, status))
        
        self.clients_count_label.config(text=f"عدد العملاء: {len(self.clients)}")
    
    def log(self, message):
        """إضافة رسالة إلى سجل العمليات"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def start_booking(self):
        """بدء عملية الحجز"""
        if not self.clients:
            messagebox.showerror("خطأ", "لا يوجد عملاء للحجز")
            return
        
        if self.is_running:
            messagebox.showwarning("تحذير", "عملية الحجز قيد التنفيذ بالفعل")
            return
        
        # تحديث الإعدادات
        self.booking_system.config.AUTO_LAUNCH_ENABLED = self.schedule_var.get()
        self.booking_system.config.RETRY_ENABLED = self.retry_var.get()
        self.booking_system.config.SEND_EMAILS = self.send_email_var.get()
        self.booking_system.config.SEND_SUMMARY_EMAIL = self.send_summary_var.get()
        
        try:
            workers = int(self.workers_entry.get())
            self.booking_system.config.MAX_WORKERS = min(workers, 100)
        except ValueError:
            pass
        
        target_date = self.date_entry.get().strip()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_running = True
        self.progress.start()
        
        self.log(f"🚀 بدء عملية الحجز لتاريخ {target_date}")
        self.log(f"📊 عدد العملاء: {len(self.clients)}، عدد الخيوط: {self.booking_system.config.MAX_WORKERS}")
        self.log(f"📧 إرسال الإيميلات: {'مفعل' if self.send_email_var.get() else 'معطل'}")
        
        thread = threading.Thread(target=self.run_booking, args=(target_date,))
        thread.daemon = True
        thread.start()
    
    def run_booking(self, target_date):
        """تشغيل الحجز في خيط منفصل"""
        try:
            self.booking_system.clients = self.clients
            self.booking_system.run(target_date)
            self.results = self.booking_system.results
            self.update_clients_list()
            
            success = sum(1 for r in self.results.values() if r.get("success", False))
            failed = len(self.results) - success
            self.log(f"🏁 انتهت عملية الحجز: ✅ نجح {success} | ❌ فشل {failed}")
            
        except Exception as e:
            self.log(f"❌ خطأ في عملية الحجز: {e}")
        
        finally:
            self.root.after(0, self.booking_finished)
    
    def booking_finished(self):
        """تنفيذ بعد انتهاء الحجز"""
        self.is_running = False
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("✅ عملية الحجز مكتملة")
    
    def stop_booking(self):
        """إيقاف عملية الحجز"""
        self.is_running = False
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("⏹️ تم إيقاف عملية الحجز")
    
    def show_results(self):
        """عرض النتائج في نافذة منفصلة"""
        if not self.results:
            messagebox.showinfo("معلومات", "لا توجد نتائج لعرضها")
            return
        
        results_window = tk.Toplevel(self.root)
        results_window.title("نتائج الحجوزات")
        results_window.geometry("800x450")
        
        columns = ('ID', 'الخدمة', 'الحالة', 'الموقع', 'التاريخ', 'الوقت', 'الخطأ')
        tree = ttk.Treeview(results_window, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(results_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)
        
        for id_num, result in self.results.items():
            service = result.get("service_id", "")
            success = "✅ نجح" if result.get("success") else "❌ فشل"
            location = result.get("location_name", "")
            ref_date = result.get("ref_date", "")
            slot = self.email_sender.convert_slot_to_time(result.get("chosen_slot", 0))
            error = result.get("error_msg", "")[:40]
            tree.insert('', 'end', values=(id_num, service, success, location, ref_date, slot, error))
        
        def export_results():
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("نتائج الحجوزات\n")
                    f.write("=" * 80 + "\n\n")
                    for id_num, result in self.results.items():
                        status = "نجح" if result.get('success') else "فشل"
                        f.write(f"{id_num}: {status}")
                        if result.get('success'):
                            f.write(f" - {result.get('location_name')} - {result.get('ref_date')}")
                        f.write("\n")
                messagebox.showinfo("نجاح", f"تم تصدير النتائج إلى {file_path}")
        
        ttk.Button(results_window, text="📤 تصدير النتائج", command=export_results).pack(pady=10)
    
    def email_settings_dialog(self):
        """نافذة إعدادات الإيميل"""
        dialog = tk.Toplevel(self.root)
        dialog.title("⚙️ إعدادات الإيميل")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # تحميل الإعدادات الحالية
        try:
            with open("email_config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {}
        
        ttk.Label(dialog, text="سيرفر SMTP:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        server_entry = ttk.Entry(dialog, width=30)
        server_entry.grid(row=0, column=1, padx=10, pady=5)
        server_entry.insert(0, config.get("smtp_server", "smtp.gmail.com"))
        
        ttk.Label(dialog, text="البريد الإلكتروني:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        email_entry = ttk.Entry(dialog, width=30)
        email_entry.grid(row=1, column=1, padx=10, pady=5)
        email_entry.insert(0, config.get("sender_email", ""))
        
        ttk.Label(dialog, text="كلمة المرور:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.grid(row=2, column=1, padx=10, pady=5)
        password_entry.insert(0, config.get("sender_password", ""))
        
        ttk.Label(dialog, text="إيميل المشرف:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        admin_entry = ttk.Entry(dialog, width=30)
        admin_entry.grid(row=3, column=1, padx=10, pady=5)
        admin_entry.insert(0, config.get("admin_email", ""))
        
        self.email_enabled_var = tk.BooleanVar(value=config.get("enabled", True))
        ttk.Checkbutton(dialog, text="✅ تفعيل إرسال الإيميلات", 
                       variable=self.email_enabled_var).grid(row=4, column=0, columnspan=2, pady=10)
        
        def test_email():
            """اختبار إعدادات الإيميل"""
            test_config = {
                "smtp_server": server_entry.get(),
                "smtp_port": 587,
                "sender_email": email_entry.get(),
                "sender_password": password_entry.get(),
                "use_tls": True,
                "admin_email": admin_entry.get() or email_entry.get()
            }
            
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                msg = MIMEMultipart()
                msg['From'] = test_config["sender_email"]
                msg['To'] = test_config["admin_email"]
                msg['Subject'] = "🧪 اختبار إعدادات الإيميل"
                msg.attach(MIMEText("تم الاتصال بنجاح!", 'plain', 'utf-8'))
                
                server = smtplib.SMTP(test_config["smtp_server"], 587)
                server.starttls()
                server.login(test_config["sender_email"], test_config["sender_password"])
                server.send_message(msg)
                server.quit()
                
                messagebox.showinfo("نجاح", "✅ تم إرسال إيميل اختبار بنجاح!")
            except Exception as e:
                messagebox.showerror("خطأ", f"❌ فشل الاتصال: {e}")
        
        ttk.Button(dialog, text="🧪 اختبار الاتصال", command=test_email).grid(row=5, column=0, columnspan=2, pady=10)
        
        def save_settings():
            config = {
                "smtp_server": server_entry.get(),
                "smtp_port": 587,
                "sender_email": email_entry.get(),
                "sender_password": password_entry.get(),
                "use_tls": True,
                "admin_email": admin_entry.get() or email_entry.get(),
                "email_subject_prefix": "[MyVisit] ",
                "email_delay_seconds": 1,
                "enabled": self.email_enabled_var.get()
            }
            with open("email_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("نجاح", "✅ تم حفظ إعدادات الإيميل")
            dialog.destroy()
        
        ttk.Button(dialog, text="💾 حفظ الإعدادات", command=save_settings).grid(row=6, column=0, columnspan=2, pady=15)

def main():
    """تشغيل الواجهة الرسومية"""
    root = tk.Tk()
    app = BookingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()