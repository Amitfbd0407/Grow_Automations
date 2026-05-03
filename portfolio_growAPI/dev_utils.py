import json
import requests
import time
import uuid
import os
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import random
from filelock import FileLock
from dev_config import ApiConfig, Url

BASE_PATH = Path(__file__).parent


class StaticFunctions:
    @staticmethod
    def get_vat_type(automation_name: str):
        name = automation_name.lower()
        match name:
            case n if any(x in n for x in ["patur", "amuta", "shitufit"]):
                return 3
            case n if any(x in n for x in ["murshe", "baam", "aguda"]):
                return random.choice([1, 2])
            case _:
                return 1

    @staticmethod
    def get_run_id():
        return str(uuid.uuid4())


    @staticmethod
    def token_identifier():
        return random.randint(1, 4294967295)

    @staticmethod
    def get_amount(automation_name: str, price1: str, price2: str):
        file_path = BASE_PATH / "amount_file.json"
        lock_path = BASE_PATH / "amount_file.json.lock"
        lock = FileLock(lock_path, timeout=1)

        with lock:
            data = {}
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8").strip()
                    data = json.loads(content) if content else {}
                except:
                    data = {}

            last_amount = data.get(automation_name)
            current_amount = str(price2) if str(last_amount) == str(price1) else str(price1)

            data[automation_name] = current_amount
            file_path.write_text(json.dumps(data, indent=4), encoding="utf-8")

        return float(current_amount)

    @staticmethod
    def normalize(val, is_amount=False):
        if val is None or val == "" or val == "N/A": return ""
        if is_amount:
            try:
                return "{:.2f}".format(float(val))
            except:
                return str(val).strip()
        return str(val).strip()

    @staticmethod
    def get_unique_id():
        return uuid.uuid4().int % 2147483647


class BasePaymentBot:
    def __init__(self, automation_name: str):
        self.unique_identifier = str(StaticFunctions.token_identifier())
        self.automation_name = automation_name
        self.run_id = StaticFunctions.get_run_id()
        self.full_response, self.request_payload = None, {}
        self.sync_data, self.process_id = None, None
        self.process_token = None
        self.process_data = {}
        self.transaction_data = {}
        self.approve_payload = {}
        self.approve_response = {}
        self.token_confirm_response = {}

        print(f"[Run ID: {self.run_id}] >>> Started: {self.automation_name}")

    def create_auth(self, amount, extra_params=None):
        print(f"[Run ID: {self.run_id}] Step: Auth Request")
        vat_type1 = StaticFunctions.get_vat_type(self.automation_name)
        vat_type2 = StaticFunctions.get_vat_type(self.automation_name)

        total_sum = float(amount)
        p1 = total_sum / 2
        p2 = total_sum - p1

        self.request_payload = {
            "userId": ApiConfig.userid,
            "apiKey": ApiConfig.apiKey,
            "sum": total_sum,
            "description": "Automation Payment",
            "pageField[fullName]": f"Test {self.run_id[:8]}",
            "pageField[phone]": ApiConfig.phone,
            "pageField[email]": Url.invoice_url,
            "notifyUrl": Url.notify_url,
            "productData[0][catalogNumber]": "8787989",
            "productData[0][quantity]": "1",
            "productData[0][price]": p1,
            "productData[0][itemDescription]": "automation product payment 1",
            "productData[0][vatType]": vat_type1,
            "productData[1][catalogNumber]": "8787989",
            "productData[1][quantity]": "1",
            "productData[1][price]": p2,
            "productData[1][itemDescription]": "automation product payment 2",
            "productData[1][vatType]": vat_type2,
            "invoiceNotifyUrl": Url.invoice_url,
            "successUrl": Url.grow_website
        }

        if extra_params:
            self.request_payload.update(extra_params)

        time.sleep(5)
        res = requests.post(Url.api_payment, data=self.request_payload)


        try:
            self.full_response = res.json()
        except Exception:
            raise Exception(f"API returned non-JSON response: {res.text}")


        if not isinstance(self.full_response, dict):
            raise Exception(f"API returned unexpected format: {self.full_response}")


        if self.full_response.get('status') != 1:
            raise Exception(f"API failure response: {json.dumps(self.full_response, indent=2, ensure_ascii=False)}")


        if 'data' in self.full_response:
            self.process_id = self.full_response['data'].get('processId')
            self.process_token = self.full_response['data'].get('processToken')
            print(f"[Run ID: {self.run_id}] Obtained ProcessID: {self.process_id}")

        return self.full_response, self.full_response.get('data', {}).get('url')

    def j4j5_or_token(self, amount, extra_params=None):
        print(f"[Run ID: {self.run_id}] Step: Settlement Execution")
        data_node = self.sync_data.get('data', self.sync_data)
        transactions = data_node.get('transactions', [])
        log = transactions[-1] if transactions else data_node

        payload = {
            "userId": ApiConfig.userid,
            "apiKey": ApiConfig.apiKey,
            "sum": amount,
            "paymentType": "2",
            "paymentNum": "1",
            "maxPaymentNum": "6",
            "description": self.request_payload.get("description", "Automation Payment")
        }

        if extra_params:
            payload.update(extra_params)

        is_token_flow = "cardToken" in log

        if is_token_flow:
            url = Url.token
            payload["cardToken"] = log["cardToken"]
            payload["transactionUniqueIdentifier"] = self.unique_identifier

        else:
            url = Url.j4_transaction
            payload.update({
                "transactionId": log.get("transactionId"),
                "transactionToken": log.get("transactionToken")
            })

        response = requests.post(url, data=payload).json()
        self.approve_response = response

        if response.get("status") != 1:
            raise Exception(f"Settlement Failed: {response.get('err')}")

        if "data" in response:
            self.transaction_data = {"status": 1, "err": "", "data": response["data"]}

        print(f"[Run ID: {self.run_id}] Settlement Request Successful.")
        return response

    def sync_and_save_data(self, page_code: str):
        print(f"[Run ID: {self.run_id}] Step: Syncing Data")
        if not self.full_response or 'data' not in self.full_response: return {}


        process_payload = {
            "userId": ApiConfig.userid,
            "apiKey": ApiConfig.apiKey,
            "processId": self.process_id,
            "processToken": self.process_token,
            "pageCode": page_code
        }
        self.process_data = requests.post(Url.process_info, data=process_payload).json()
        self.sync_data = self.process_data

        tx = self.process_data.get('data', {}).get('transactions', [{}])[-1]

        tx_info_payload = {
            "userId": ApiConfig.userid,
            "apiKey": ApiConfig.apiKey,
            "pageCode": page_code,
            "transactionId": tx.get("transactionId"),
            "transactionToken": tx.get("transactionToken")
        }
        self.transaction_data = requests.post(Url.transaction_info, data=tx_info_payload).json()

        print(f"[Run ID: {self.run_id}] Process and Transaction data saved separately.")
        return self.process_data

    def approve_transaction(self, page_code: str, extra_params=None):
        print(f"[Run ID: {self.run_id}] Step: API Approve")

        tx = self.sync_data.get('data', {}).get('transactions', [{}])[-1]

        if "token" in self.automation_name.lower():
            print(f"Logic: Token Transaction Detected")
            url_to_call = Url.token_transaction
            payload = {
                "cardToken": tx.get("cardToken") or self.sync_data.get("cardToken"),
                "transactionUniqueIdentifier": self.unique_identifier,
            }
        else:
            print(f"Logic: Standard Transaction Detected")
            url_to_call = Url.approve_transaction
            payload = {
                "userId": ApiConfig.userid,
                "apiKey": ApiConfig.apiKey,
                "pageCode": page_code,
                "transactionId": tx.get("transactionId"),
                "transactionToken": tx.get("transactionToken"),
                "sum": tx.get("sum"),
                "paymentType": tx.get("paymentType", "2"),
                "paymentsNum": tx.get("paymentsNum", "1"),
                "allPaymentsNum": tx.get("allPaymentsNum", "1"),
                "fullName": tx.get("fullName"),
                "payerPhone": tx.get("payerPhone"),
                "payerEmail": tx.get("payerEmail"),
                "cardSuffix": tx.get("cardSuffix"),
                "cardBrand": tx.get("cardBrand"),
                "cardExp": tx.get("cardExp"),
                "asmachta": tx.get("asmachta"),
                "description": tx.get("description")
            }

        if extra_params:
            payload.update(extra_params)

        self.approve_payload = payload

        try:
            res = requests.post(url_to_call, data=payload).json()
            self.approve_response = res
            print(f"[Run ID: {self.run_id}] Approve Result: {res.get('status')} (URL: {url_to_call})")
            return res
        except Exception as e:
            print(f"Error during API Approve: {e}")
            return {"status": "error", "message": str(e)}

class refund_sms(BasePaymentBot):
    def RefundTransaction(self, page_code: str, user_id: str):
        print(f"[Run ID: {self.run_id}] Step: Refund")
        data = self.sync_data.get("data", {})
        transactions = data.get("transactions", [])
        refund = transactions[-1] if transactions else data
        payload = {
            "userId": user_id,
            "apiKey": ApiConfig.apiKey,
            "pageCode": page_code,
            "refundSum": "{:.2f}".format(float(refund.get("sum", 0))),
            "transactionId": refund.get("transactionId"),
            "transactionToken": refund.get("transactionToken")
        }
        requests.post(Url.refund_info, data=payload)
        print(f"[Run ID: {self.run_id}] Refund Processed.")

    def sms_check(self, business_name):
        load_dotenv(dotenv_path=BASE_PATH / "sensitive.env")
        expected_sum = "{:.2f}".format(float(self.request_payload["sum"]))
        start_search = (datetime.datetime.now(ZoneInfo("Asia/Jerusalem")) - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(10):
            try:
                sms_res = requests.get(Url.sms_api, params={"user": os.getenv("SMS_USER"), "password": os.getenv("SMS_PASSWORD"), "start_date": start_search}).json()
                messages = sms_res.get("inbound_message", [])
                if isinstance(messages, dict): messages = messages.values()
                for msg in messages:
                    if business_name.lower() in msg.get("message", "").lower() and expected_sum in msg.get("message", ""):
                        print(f"[Run ID: {self.run_id}] SUCCESS: SMS Confirmation found!")
                        return True
            except: pass
            time.sleep(15)
        raise Exception("SMS not found")

    def update_standing_order(self, user_id: str, status="2"):
        print(f"[Run ID: {self.run_id}] Step: Update Direct Debit (Status: {status})")
        data = self.sync_data.get("data", {})
        transactions = data.get("transactions", [])
        tx = transactions[-1] if transactions else data

        payload = {
            "userId": user_id,
            "apiKey": ApiConfig.apiKey,
            "transactionToken": tx.get("transactionToken"),
            "transactionId": tx.get("transactionId"),
            "asmachta": tx.get("asmachta"),
            "fullName": tx.get("fullName"),
            "phone": tx.get("payerPhone"),
            "email": tx.get("payerEmail"),
            "changeStatus": status,
            "updateCard": "1"
        }

        res = requests.post(Url.recurring_refund, data=payload)
        res_json = res.json()

        if res_json.get("status") != 1:
            error_msg = res_json.get("err", "Unknown Error")
            raise Exception(f"Update Direct Debit Failed: {error_msg}")

        print(f"[Run ID: {self.run_id}] Update Direct Debit Success: {res_json}")
        return res_json