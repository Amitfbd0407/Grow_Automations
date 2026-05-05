import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_structure import GrowAutomationBase, CreditCard
from search_and_compare import TransactionAuditManager
from config import Mapping
from utils import TransactionFlowHelpers
from alerts import update_status_and_check_alert


class RecurringPaymentBot(GrowAutomationBase):
    def __init__(self, headless: bool = False):
        super().__init__(headless=headless)
        self.customer_name = TransactionFlowHelpers.generate_random_customer_name()
        self.automation_name = "recurring_dashboard_test"
        self.current_step = "Initialization"
        self.refund_asmachta = None
        self.db_record = None

        self.biz_conf = {"userId": "AutomationBot"}

    def start(self):

        try:
            self.current_step = "Login"
            self.login()
            print(f"Generated Name for Automation: {self.customer_name}")

            self.current_step = "Create Recurring Transaction"
            recurring_steps = [
                {"action": "wait", "value": 2},
                {"action": "click", "selector": f"text={Mapping.new_transaction}"},
                {"action": "click", "selector": f"text={Mapping.recurring_payment}"},
                {"action": "wait", "value": 2},
                {"action": "click", "selector": f"text={Mapping.write_amount}"},
                {"action": "fill", "selector": "input[name='amountToCharge']", "value": "0.2"},
                {"action": "fill", "selector": "textarea[name='chargeFor']", "value": "Recurring Automation Test"},
                {"action": "click", "selector": f"text={Mapping.temporary_customer}"},
                {"action": "fill", "selector": Mapping.full_name, "value": self.customer_name},
                {"action": "fill", "selector": f"{Mapping.phone}", "value": "0500000000"},
                {"action": "fill", "selector": f"{Mapping.input_email}", "value": "test@test.com"},
                {"action": "click", "selector": Mapping.recurring_number_dropdown, "iframe": False},
                {"action": "wait", "value": 1},
                {"action": "click", "selector": Mapping.recurring_number_option_12, "iframe": False},
                {"action": "click", "selector": Mapping.credit_card},
                {"action": "wait", "value": 5},
            ]
            self.handler.execute_workflow_steps(recurring_steps)

            self.current_step = "Fill Credit Card (Iframe)"
            CreditCard(self.page)

            self.current_step = "Database Audit"
            audit_manager = TransactionAuditManager(self.page)

            self.db_record = audit_manager.execute_comparison_audit(self.customer_name, "recurring")

            #self.current_step = "Execute Refund"
            #TransactionFlowHelpers.execute_refund_flow(self.handler, self.customer_name)

            #self.current_step = "Verify Refund & Extract Reference"
           #self.refund_asmachta = TransactionFlowHelpers.validate_refund_and_get_reference(self.handler,
                                                                                            #self.customer_name)
            #print(f"Refund Reference Captured: {self.refund_asmachta}")


            self.current_step = "Navigate and Click Recurring Row"
            print(f"[PROCESS] Going to Recurring Payments and clicking on {self.customer_name}")

            TransactionFlowHelpers.cancel_recurring_payment(self.handler, self.customer_name, 3)



            update_status_and_check_alert(self, status="SUCCESS", step="Completed")
            print(f"--- SUCCESS: {self.automation_name} completed ---")
            return True

        except Exception as e:
            print(f"!!! Error in {self.automation_name} at step {self.current_step}: {e}")
            update_status_and_check_alert(self, status="FAIL", step=self.current_step, reason=str(e))
            return False


if __name__ == "__main__":
    bot = RecurringPaymentBot(headless=False)
    success = bot.start()

    time.sleep(5)
    sys.exit(0 if success else 1)