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
from dev_config import BusinessData, Amount, Fields, Descriptions, CreditInfo, ChargeType, ApiConfig
from dev_compare_hook_db import run_full_audit, SettlementAudit


class CgTokenBot(refund_sms):
    def __init__(self, business_identifier):
        self.biz_conf = BusinessData.MAP.get(business_identifier)
        if not self.biz_conf:
            raise ValueError(f"Config missing for: {business_identifier}")

        super().__init__(f"dev_cc_token_{business_identifier}")

        self.sync_data = None
        self.current_step = "Initialization"

    def start(self):
        u_id = self.biz_conf.get("userId", "N/A")
        p_code = self.biz_conf.get("cc", "N/A")

        try:
            self.current_step = "Setup"
            ApiConfig.userid = u_id
            amount = StaticFunctions.get_amount(self.automation_name, Amount.token_cc1, Amount.token_cc2)

            self.current_step = "API Auth (Token Creation)"
            extra = {
                "pageCode": p_code,
                "userId": u_id,
                "description": Descriptions.token,
                "chargeType": ChargeType.token,
                "cField1": Fields.token_cc_1,
                "cField2": Fields.token_cc_2,
                "maxPaymentNum": "6",
                "paymentNum": "1",
                "saveCardToken": "1"
            }

            auth_res = self.create_auth(amount, extra)
            _, payment_url = auth_res if isinstance(auth_res, tuple) else (auth_res, None)

            if not payment_url:
                raise Exception(f"API Auth Failed")

            self.current_step = "UI Payment (Generate Token)"
            Fields_and_clicks.run(payment_url, CreditInfo, self, pre_steps=[{"action": "wait", "value": "5"}])

            self.current_step = "Sync Token Data"
            self.sync_and_save_data(p_code)
            run_full_audit(self)

            self.current_step = "Settlement (Charge with Token)"
            settlement_extra = {
                "userId": u_id,
                "apiKey": ApiConfig.apiKey,
                "pageCode": p_code
            }
            self.j4j5_or_token(amount, extra_params=settlement_extra)


            self.sync_and_save_data(p_code)

            self.current_step = "API Approve"
            approve_params = {
                "userId": u_id,
                "apiKey": ApiConfig.apiKey
            }
            self.approve_transaction(p_code, extra_params=approve_params)

            time.sleep(3)

            self.current_step = "Final Settlement Audit"
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