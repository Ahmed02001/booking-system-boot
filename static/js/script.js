// static/js/script.js

// ============= دوال عامة =============

function showNotification(message, type = "info") {
  const colors = {
    success: "#4CAF50",
    error: "#dc3545",
    warning: "#ffc107",
    info: "#17a2b8",
  };

  const notification = document.createElement("div");
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${colors[type] || colors.info};
        color: #fff;
        border-radius: 8px;
        font-weight: 500;
        z-index: 9999;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: slideIn 0.3s;
        max-width: 400px;
    `;
  notification.textContent = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = "slideOut 0.3s";
    setTimeout(() => notification.remove(), 300);
  }, 4000);
}

// إضافة الأنيميشن
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// ============= دوال التاريخ =============

function formatDate(date) {
  return new Date(date).toLocaleDateString("ar-EG", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString("ar-EG", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getToday() {
  return new Date().toISOString().split("T")[0];
}

function getFutureDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().split("T")[0];
}

// ============= دوال التحقق =============

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateIdNumber(id) {
  return /^[0-9]{9}$/.test(id);
}

// ============= دوال التحميل =============

function showLoading() {
  const loader = document.createElement("div");
  loader.id = "globalLoader";
  loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9998;
    `;
  loader.innerHTML = `
        <div style="
            background: #fff;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
        ">
            <div style="
                width: 50px;
                height: 50px;
                border: 5px solid #f3f3f3;
                border-top: 5px solid #4CAF50;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            "></div>
            <div style="font-size: 16px; color: #1a1a2e;">جاري التحميل...</div>
        </div>
    `;
  document.body.appendChild(loader);

  // إضافة أنيميشن الدوران
  const spinStyle = document.createElement("style");
  spinStyle.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
  document.head.appendChild(spinStyle);
}

function hideLoading() {
  const loader = document.getElementById("globalLoader");
  if (loader) loader.remove();
}

// ============= دوال السجلات =============

function addLogMessage(message, type = "info") {
  const container = document.getElementById("logContainer");
  if (!container) return;

  const time = formatTime(new Date());
  const logEntry = document.createElement("div");
  logEntry.className = "log-entry";

  const icons = {
    success: "✅",
    error: "❌",
    warning: "⚠️",
    info: "ℹ️",
  };

  logEntry.textContent = `[${time}] ${icons[type] || ""} ${message}`;
  container.appendChild(logEntry);
  container.scrollTop = container.scrollHeight;
}

// ============= دوال التصدير =============

function exportData(data, filename = "export.json") {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function exportToCSV(data, filename = "export.csv") {
  if (!data || data.length === 0) {
    alert("لا توجد بيانات للتصدير");
    return;
  }

  const headers = Object.keys(data[0]);
  const csv = [
    headers.join(","),
    ...data.map((row) =>
      headers.map((h) => JSON.stringify(row[h] || "")).join(","),
    ),
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

// ============= دوال الإحصائيات =============

function calculateStats(data) {
  if (!data || data.length === 0) {
    return { total: 0, success: 0, failed: 0, successRate: 0 };
  }

  const total = data.length;
  const success = data.filter((item) => item.success).length;
  const failed = total - success;
  const successRate = total > 0 ? ((success / total) * 100).toFixed(1) : 0;

  return { total, success, failed, successRate };
}

// ============= تهيئة الصفحة =============

document.addEventListener("DOMContentLoaded", function () {
  // تعيين التاريخ الافتراضي في حقول التاريخ
  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach((input) => {
    if (!input.value) {
      input.value = getFutureDate(3);
    }
  });

  console.log("✅ تم تحميل النظام بنجاح");
});
