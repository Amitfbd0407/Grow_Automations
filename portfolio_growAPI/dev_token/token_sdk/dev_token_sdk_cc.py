import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from dev_alerts import update_status_and_check_alert
from dev_flow_structure import Fields_and_clicks
from dev_utils import refund_sms, StaticFunctions
from dev_config import BusinessData, Amount, Fields, Descriptions, CreditInfo, ChargeType, ApiConfig, Url
from dev_compare_hook_db import run_full_audit, SettlementAudit

class CgTokenBot(refund_sms):
    def __init__(self, business_identifier):
        self.biz_conf = BusinessData.MAP.get(business_identifier)
        if not self.biz_conf:
            raise ValueError(f"Config missing for: {business_identifier}")
        super().__init__(f"dev_sdk_token_{business_identifier}")
        self.current_step = "Initialization"

    def start(self):
        u_id = self.biz_conf.get("userId", "N/A")
        p_code = self.biz_conf.get("sdk", "N/A")
        try:
            self.current_step = "Setup"
            ApiConfig.userid = u_id
            amount = StaticFunctions.get_amount(self.automation_name, Amount.token_sdk1, Amount.token_sdk2)

            self.current_step = "API Auth (Token Creation)"
            extra = {"pageCode": p_code,
                     "userId": u_id,
                     "description": Descriptions.token,
                     "chargeType": ChargeType.token,
                     "cField1": Fields.token_sdk_1,
                     "cField2": Fields.token_sdk_2,
                     "maxPaymentNum": "6",
                     "paymentNum": "1",
                     "saveCardToken": "1"}

            auth_res = self.create_auth(amount, extra)
            full_res = auth_res[0] if isinstance(auth_res, tuple) else auth_res
            sdk_auth_code = full_res.get('data', {}).get('authCode')

            if not sdk_auth_code:
                raise Exception(f"API Auth Failed: {full_res.get('err')}")

            self.current_step = "UI Payment (SDK)"
            sdk_pre_steps = [
                {"action": "click", "selector": "#dev", "iframe": False},
                {"action": "select", "selector": "#version", "value": "1.0.9", "iframe": False},
                {"action": "wait", "value": "1"},
                {"action": "fill", "selector": "#hash", "value": sdk_auth_code, "iframe": False},
                {"action": "wait", "value": "1"},
                {"action": "click", "selector": "#run_btn", "iframe": False},
                {"action": "wait", "value": "4"},
                {"action": "click", "selector": "#purchase", "iframe": False},
                {"action": "wait", "value": "4"},
                {"action": "click", "selector": "img[data-alt='sdk_image_alt__pay_with_credit']", "iframe": False},
                {"action": "wait", "value": "8"}
            ]

            Fields_and_clicks.run(url=Url.sdk_url, credit_info=CreditInfo, bot=self, pre_steps=sdk_pre_steps)

            self.current_step = "Sync and Audit Token"
            self.sync_and_save_data(p_code)
            run_full_audit(self)

            self.current_step = "Settlement"
            self.j4j5_or_token(amount, extra_params={"userId": u_id, "apiKey": ApiConfig.apiKey, "pageCode": p_code})


            self.sync_and_save_data(p_code)
            self.approve_transaction(p_code, extra_params={"userId": u_id, "apiKey": ApiConfig.apiKey})
            time.sleep(3)

            self.current_step = "Final Audit"
            SettlementAudit.run(self)

            self.current_step = "Refund"
            self.RefundTransaction(p_code, u_id)

            update_status_and_check_alert(self, status="SUCCESS", step="Completed")
            print(f"--- SUCCESS: {self.automation_name} completed ---")
            return True

        except Exception as e:
            print(f"!!! Error in {self.automation_name} at step {self.current_step}: {e}")
            update_status_and_check_alert(self, status="FAIL", step=self.current_step, reason=str(e))
            return False

if __name__ == "__main__":
    target_biz = sys.argv[1] if len(sys.argv) > 1 else "patur"
    bot = CgTokenBot(target_biz)
    success = bot.start()
    sys.exit(0 if success else 1)