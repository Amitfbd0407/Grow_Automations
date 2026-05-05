import mysql.connector
import json
import re
import datetime
from zoneinfo import ZoneInfo
from flow_structure import WebAutomationHandler
from config import Db


class TransactionAuditManager:

    def __init__(self, page):
        self.page = page
        self.automation_handler = WebAutomationHandler(self.page)

    @staticmethod
    def parse_numeric_amount(amount_string):
        if not amount_string:
            return 0.0
        cleaned_value = re.sub(r'[^\d.]', '', amount_string)
        try:
            return float(cleaned_value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _validate_recurring_entry(business_client_id):
        try:
            connection = mysql.connector.connect(
                host=Db.host, user=Db.user, password=Db.password,
                database=Db.DB_NAME, port=int(Db.DB_PORT)
            )
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id FROM tb_recurring_debit WHERE payment_business_client_id = %s LIMIT 1"
            cursor.execute(query, (business_client_id,))
            recurring_record = cursor.fetchone()
            connection.close()
            return recurring_record
        except:
            return None

    @staticmethod
    def get_transaction_from_database(full_name: str):
        try:

            first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, "")

            connection = mysql.connector.connect(
                host=Db.host,
                user=Db.user,
                password=Db.password,
                database=Db.DB_NAME,
                port=int(Db.DB_PORT)
            )

            cursor = connection.cursor(dictionary=True)


            sql_query = """
                    SELECT * FROM tb_tenants_config 
                    WHERE payer_first_name=%s AND payer_last_name=%s 
                    ORDER BY id DESC LIMIT 1
                """

            cursor.execute(sql_query, (first_name, last_name))
            database_record = cursor.fetchone()
            connection.close()

            return database_record

        except Exception as error:
            print(f"Database Error: {error}")
            return None


    def execute_comparison_audit(self, customer_name: str, automation_identifier: str):
        navigation_steps = [
            {"action": "wait", "value": 3},
            {"action": "click", "selector": 'a:has-text("עסקאות")', "iframe": False},
            {"action": "wait", "value": 5},
            {"action": "reload"},
            {"action": "wait", "value": 5},
            {"action": "verify", "value": customer_name}
        ]
        self.automation_handler.execute_workflow_steps(navigation_steps)

        transaction_row = self.page.locator("tr").filter(has_text=customer_name).first
        columns = transaction_row.locator("td")

        website_data = {
            "date": columns.nth(0).inner_text().strip(),
            "customer_name": columns.nth(1).inner_text().strip(),
            "phone": columns.nth(2).inner_text().strip(),
            "amount_raw": columns.nth(5).inner_text().strip(),
            "status": columns.nth(6).inner_text().strip()
        }

        database_record = self.get_transaction_from_database(customer_name)

        print("\n" + "═" * 80)
        print(f"🔍 AUDIT REPORT: {customer_name}")
        print("═" * 80)

        if database_record:
            israel_timezone = ZoneInfo("Asia/Jerusalem")
            db_date_formatted = datetime.datetime.fromtimestamp(
                database_record['payment_date'],
                tz=datetime.timezone.utc
            ).astimezone(israel_timezone).strftime('%d/%m/%Y')

            status_translation = {2: "חוייב", 1: "ממתין", 3: "בוטל"}
            db_status_text = status_translation.get(database_record['status'], "אחר")

            website_amount = self.parse_numeric_amount(website_data["amount_raw"])
            database_amount = float(database_record.get('payment_sum', 0))

            print(f"{'Parameter':<18} | {'Website (UI)':<22} | {'Database (DB)':<22} | Status")
            print("-" * 80)

            audit_fields = [
                ("Customer Name", website_data["customer_name"], customer_name),
                ("Phone Number", website_data["phone"].replace("-", ""), database_record['payer_phone']),
                ("Transaction Date", website_data["date"], db_date_formatted),
                ("Payment Status", website_data["status"], db_status_text),
                ("Final Amount", website_amount, database_amount)
            ]

            for label, ui_val, db_val in audit_fields:
                is_match = str(ui_val) == str(db_val)
                print(f"{label:<18} | {str(ui_val):<22} | {str(db_val):<22} | {'✅ PASS' if is_match else '❌ FAIL'}")


            if "recurring" in automation_identifier.lower():
                client_id = database_record.get('payment_business_client_id')
                print("-" * 80)
                print(f"📡 Recurring detected. Checking tb_recurring_debit for ID: {client_id}")
                if self._validate_recurring_entry(client_id):
                    print(f"✅ SUCCESS: Corresponding recurring record found.")
                else:
                    print(f"❌ FAILURE: No record found in recurring table.")

            print("\n" + "-" * 80)
            print("📦 RAW DATABASE JSON:")
            print(json.dumps(database_record, indent=4, ensure_ascii=False, default=str))
        else:
            print("Critical Error: Transaction record not found in Database.")

        print("═" * 80 + "\n")
        return database_record