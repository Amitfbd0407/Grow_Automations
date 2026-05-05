import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_structure import GrowAutomationBase, CreditCard
from search_and_compare import TransactionAuditManager
from config import Mapping
from utils import TransactionFlowHelpers
from alerts import update_status_and_check_alert


class InvoiceDownloaderBot(GrowAutomationBase):
    def __init__(self, headless: bool = False):
        super().__init__(headless=headless)
        self.customer_name = TransactionFlowHelpers.generate_random_customer_name()
        self.automation_name = "regular_invoice_test"
        self.current_step = "Initialization"
        self.refund_asmachta = None
        self.biz_conf = {"userId": "AutomationBot"}

    def start(self):
        try:
            self.current_step = "Login"
            self.login()
            print(f"Generated Name for Automation: {self.customer_name}")

            self.current_step = "Create Regular Transaction"
            regular_steps = [
                {"action": "click", "selector": f"text={Mapping.new_transaction}"},
                {"action": "wait", "value": 2},
                {"action": "click", "selector": f"label={Mapping.regular_payment}"},
                {"action": "click", "selector": f"text={Mapping.write_amount}"},
                {"action": "fill", "selector": "input[name='amountToCharge']", "value": "0.1"},
                {"action": "fill", "selector": "textarea[name='chargeFor']", "value": "Regular Automation Test"},
                {"action": "click", "selector": f"text={Mapping.temporary_customer}"},
                {"action": "fill", "selector": Mapping.full_name, "value": self.customer_name},
                {"action": "fill", "selector": f"{Mapping.phone}", "value": "0500000000"},
                {"action": "fill", "selector": f"{Mapping.input_email}", "value": "test@test.com"},
                {"action": "click", "selector": Mapping.payment_number},
                {"action": "click", "selector": "role=option[name='1']"},
                {"action": "click", "selector": Mapping.credit_card},
                {"action": "wait", "value": 5},
            ]
            self.handler.execute_workflow_steps(regular_steps)

            self.current_step = "Fill Credit Card (Iframe)"
            CreditCard(self.page)

            self.current_step = "Database Audit"
            audit_manager = TransactionAuditManager(self.page)
            audit_manager.execute_comparison_audit(self.customer_name, "regular")

            self.current_step = "Execute Refund"
            TransactionFlowHelpers.execute_refund_flow(self.handler, self.customer_name)

            self.current_step = "Close Refund Modal"
            print("[PROCESS] לוחץ על כפתור חזרה לסגירת פרטי עסקה")
            try:
                self.page.get_by_text("תודה").click(timeout=3000)
            except:
                pass


            back_btn_selector = "span.back-button_button-text__t_lEf"
            self.page.wait_for_selector(back_btn_selector, state="visible", timeout=10000)
            self.page.locator(back_btn_selector).click(force=True)
            self.page.wait_for_timeout(2000)

            self.current_step = "Verify Refund & Extract Reference"
            self.refund_asmachta = TransactionFlowHelpers.validate_refund_and_get_reference(self.handler,
                                                                                            self.customer_name)
            print(f"Refund Reference Captured: {self.refund_asmachta}")


            update_status_and_check_alert(self, status="SUCCESS", step="Completed")
            print(f"--- SUCCESS: {self.automation_name} completed ---")
            return True

        except Exception as e:
            print(f"!!! Error in {self.automation_name} at step {self.current_step}: {e}")
            update_status_and_check_alert(self, status="FAIL", step=self.current_step, reason=str(e))
            return False


if __name__ == "__main__":
    bot = InvoiceDownloaderBot(headless=False)
    success = bot.start()

    time.sleep(5)
    sys.exit(0 if success else 1)