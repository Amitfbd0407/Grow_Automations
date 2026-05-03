import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from dev_alerts import update_status_and_check_alert
from dev_flow_structure import Fields_and_clicks
from dev_utils import refund_sms, StaticFunctions
from dev_config import BusinessData, Amount, Fields, Descriptions, CreditInfo, ChargeType, ApiConfig
from dev_compare_hook_db import run_full_audit


class CgJ4j5Bot(refund_sms):
    def __init__(self, business_identifier):
        self.biz_conf = BusinessData.MAP.get(business_identifier)
        if not self.biz_conf:
            raise ValueError(f"Config missing for: {business_identifier}")

        super().__init__(f"dev_cc_j4j5_{business_identifier}")
        self.current_step = "Initialization"

    def start(self):
        u_id = self.biz_conf.get("userId", "N/A")
        p_code = self.biz_conf.get("cc", "N/A")

        try:
            self.current_step = "Setup"
            ApiConfig.userid = u_id

            amount = StaticFunctions.get_amount(self.automation_name, Amount.j4j5_cc1, Amount.j4j5_cc2)

            self.current_step = "API Auth (J5)"
            extra = {
                "pageCode": p_code,
                "userId": u_id,
                "description": f"{Descriptions.cg} J4/J5 Flow",
                "chargeType": ChargeType.j4j5,
                "cField1": Fields.j4j5_cc_1,
                "cField2": Fields.j4j5_cc_2,
                "maxPaymentNum": "6",
                "paymentNum": "1"
            }

            auth_res = self.create_auth(amount, extra)

            if isinstance(auth_res, tuple):
                full_res, payment_url = auth_res
            else:
                full_res, payment_url = auth_res, None

            if not payment_url:
                err = full_res.get('err') if isinstance(full_res, dict) else str(full_res)
                raise Exception(f"API Auth Failed: {err}")

            self.current_step = "UI Payment"

            p_steps = [{"action": "wait", "value": "5"}]

            Fields_and_clicks.run(payment_url, CreditInfo, self, pre_steps=p_steps)

            self.current_step = "Sync Suspended"
            self.sync_and_save_data(p_code)

            self.current_step = "Audit Suspended"
            audit_errors = run_full_audit(self)
            if audit_errors:
                report = "\n".join(audit_errors)
                update_status_and_check_alert(self, status="FAIL", step="Audit Suspended",
                                              reason=f"Mismatch: {audit_errors[0]}", audit_report=report)
                raise Exception(f"Audit Mismatch (Suspended): {audit_errors[0]}")

            self.current_step = "Settlement (J4)"

            self.j4j5_or_token(amount)

            self.current_step = "Sync Final"
            self.sync_and_save_data(p_code)

            self.current_step = "Audit Final"
            audit_errors = run_full_audit(self)
            if audit_errors:
                report = "\n".join(audit_errors)
                update_status_and_check_alert(self, status="FAIL", step="Audit Final",
                                              reason=f"Mismatch: {audit_errors[0]}", audit_report=report)
                raise Exception(f"Audit Mismatch (Final): {audit_errors[0]}")

            self.current_step = "SMS Check"
            self.sms_check(business_name=self.biz_conf["sms_name"])

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
    bot = CgJ4j5Bot(target_biz)
    success = bot.start()
    sys.exit(0 if success else 1)