import datetime
import requests
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
from dev_config import Url

BASE_PATH = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_PATH / "dev_sensitive.env")

DB_SETTINGS = {
    "host": "localhost",
    "database": "live_automations",
    "user": "postgres",
    "password": os.getenv("LOCAL_DB"),
    "port": "5432"
}

MAKE_WEBHOOK_URL = Url.glassix_email
TARGET_EMAIL = "amitb@grow.business"


def send_to_make_webhook(subject, automation_name, status, step="N/A", reason="", details=""):
    now_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    header_color = "#d32f2f" if status == "FAIL" else "#2e7d32"
    title = "Automation Failure" if status == "FAIL" else "Automation Recovered"
    status_icon = "❌" if status == "FAIL" else "✅"

    html_content = f"""
    <div dir="ltr" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; color: #333;">
        <div style="background-color: {header_color}; color: white; padding: 15px; font-size: 18px; font-weight: bold;">
            {status_icon} {title}: {automation_name}
        </div>
        <div style="padding: 20px; line-height: 1.6;">
            <p style="margin: 5px 0;"><b>Automation:</b> {automation_name}</p>
            <p style="margin: 5px 0;"><b>Time:</b> {now_time}</p>
            <p style="margin: 5px 0;"><b>Step:</b> {step}</p>
            <p style="margin: 5px 0; color: #d32f2f;"><b>Reason:</b> {reason}</p>
        </div>
    """
    if details and str(details).strip():
        html_content += f"""
        <div style="padding: 0 20px 20px 20px;">
            <hr style="border: 0; border-top: 1px solid #eee; margin-bottom: 15px;">
            <b style="font-size: 14px;">Detailed Audit Log:</b>
            <div style="background-color: #f4f4f4; border: 1px solid #ddd; padding: 10px; margin-top: 10px; font-family: 'Courier New', monospace; font-size: 12px; white-space: pre; overflow-x: auto;">
{details}
            </div>
        </div>"""
    html_content += "</div>"

    payload = [{"mail": TARGET_EMAIL, "name": automation_name, "header": subject, "message": html_content,
                "tag1": f"Status: {status}"}]
    try:
        requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=15)
    except Exception as e:
        print(f"Webhook Error: {e}")


def update_status_and_check_alert(bot_or_name, status, step="N/A", reason="", audit_report=""):
    if hasattr(bot_or_name, 'automation_name'):
        bot = bot_or_name
        name = bot.automation_name
        user_id = bot.biz_conf.get("userId", "N/A")
        page_code = bot.biz_conf.get("cg", "N/A")
        proc_id = getattr(bot, 'process_id', 'N/A')
        proc_token = getattr(bot, 'process_token', 'N/A')
        current_step = getattr(bot, 'current_step', step)
    else:
        name = str(bot_or_name)
        user_id, page_code, proc_id, proc_token, current_step = "N/A", "N/A", "N/A", "N/A", step

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        cursor = conn.cursor()

        # check the automation name last status
        cursor.execute("SELECT last_status FROM automation_status WHERE automation_name = %s ORDER BY id DESC LIMIT 1",
                       (name,))
        row = cursor.fetchone()
        old_status = row[0] if row else None

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if status == "FAIL" and old_status != "FAIL":
            send_to_make_webhook(f"Failure: {name}", name, "FAIL", current_step, reason, audit_report)

        elif status == "SUCCESS" and old_status == "FAIL":
            # send success mail if the last automation failed
            cursor.execute("""
                SELECT last_step 
                FROM automation_status 
                WHERE automation_name = %s AND last_status = 'FAIL' 
                ORDER BY id DESC LIMIT 1
            """, (name,))
            fail_row = cursor.fetchone()
            actual_failed_step = fail_row[0] if fail_row else "Unknown Step"


            send_to_make_webhook(f"Recovered: {name}", name, "SUCCESS", actual_failed_step, "Automation back to normal",
                                 audit_report)

        # new automation status
        cursor.execute('''INSERT INTO automation_status 
                          (automation_name, userId, pageCode, processId, processToken, last_step, last_status, reason, last_updated)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                       (name, user_id, page_code, proc_id, proc_token, current_step, status, reason, now))
        conn.commit()
    except Exception as e:
        print(f"Database Error in PostgreSQL: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()