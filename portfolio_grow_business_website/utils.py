import random
import string
from biz_website.config import Mapping


class TransactionFlowHelpers:


    @staticmethod
    def generate_random_customer_name():
        def generate_string(length):
            return ''.join(random.choices(string.ascii_lowercase, k=length)).capitalize()

        return f"{generate_string(5)} {generate_string(7)}"


    @staticmethod
    def execute_refund_flow(handler, customer_name: str):
        print(f"[PROCESS] Flow: Initiating refund for {customer_name}")

        selector = f".table_value-wrapper___91gO >> text={customer_name}"
        handler.page.locator(selector).first.click(force=True)
        handler.page.wait_for_timeout(2000)

        handler.page.click(Mapping.refund_btn, force=True)
        handler.page.wait_for_timeout(3000)

        handler.page.click(Mapping.approve_refund_btn, force=True)
        handler.page.wait_for_timeout(4000)

        print(f"[SUCCESS] Refund flow completed for {customer_name}")



    @staticmethod
    def validate_refund_and_get_reference(handler, customer_name: str):

        try:
            print("[PROCESS] trying to press the thank you after refund")
            try:
                handler.page.get_by_text("תודה").click(timeout=5000)
                handler.page.wait_for_timeout(1000)
            except:
                print("[INFO] thank you btn has been clicked or hasnt shown yet.")


            print("[PROCESS] press the transaction button")
            back_btn = "span.back-button_button-text__t_lEf"
            handler.page.wait_for_selector(back_btn, timeout=5000)
            handler.page.locator(back_btn).click(force=True)

            handler.page.wait_for_timeout(3000)

            selector = f"div.table_value-wrapper___91gO:has-text('{customer_name}')"
            handler.page.wait_for_selector(selector, state="visible", timeout=10000)
            handler.page.locator(selector).first.click()
            handler.page.wait_for_timeout(2000)

            ref_selector = 'dl:has(dt:text-is("מספר אסמכתא")) dd'
            handler.page.wait_for_selector(ref_selector, timeout=5000)
            reference = handler.page.locator(ref_selector).inner_text()

            print(f"[SUCCESS] אסמכתא חולצה בהצלחה: {reference}")
            return reference

        except Exception as e:
            print(f"[ERROR] error in confirmation process: {e}")

            handler.page.reload()
            return "Reference Check Failed - Page Reloaded"

    @staticmethod
    def cancel_recurring_payment(handler, customer_name, method_type=1):

        match method_type:
            case 1:
                print(f"[ACTION] press the recurring option on the page")

                handler.page.wait_for_selector(Mapping.recurring_menu_link)
                handler.page.click(Mapping.recurring_menu_link, force=True)
                handler.page.wait_for_timeout(3000)

                selector = f".table_value-wrapper___91gO >> text={customer_name}"
                handler.page.locator(selector).first.click()

                handler.page.click(Mapping.inside_stop_recurring_btn, force=True)
                handler.page.wait_for_timeout(4000)

                print("[ACTION] press the final button on the page")
                handler.page.click(Mapping.confirm_stop_btn, force=True)

                handler.page.wait_for_timeout(3000)
                handler.page.click(Mapping.thank_you_btn, force=True)
                print(f"[SUCCESS] recurring transaction {customer_name} has been cancelled")

            case 2:
                print(f"[ACTION] Method 2 for {customer_name}")

                handler.page.wait_for_selector(Mapping.recurring_menu_link)
                handler.page.click(Mapping.recurring_menu_link, force=True)
                handler.page.wait_for_timeout(3000)

                handler.page.locator("tr", has_text=customer_name).get_by_label("הצג/הסתר אפשרויות").first.click()
                handler.page.wait_for_timeout(1000)

                handler.page.get_by_text("עצירת הוראת קבע").first.click()
                handler.page.wait_for_timeout(1000)

                handler.page.get_by_text("כן, עצירה").first.click()

                handler.page.wait_for_timeout(2000)
                handler.page.click(Mapping.thank_you_btn, force=True)
                print(f"[SUCCESS] Method 2 finished for {customer_name}")



            case 3:
                print(f"[PROCESS] Flow: Initiating refund for {customer_name}")

                handler.page.locator(f".table_value-wrapper___91gO >> text={customer_name}").first.click(force=True)

                handler.page.wait_for_timeout(2000)

                handler.page.click(Mapping.refund_btn, force=True)

                handler.page.wait_for_timeout(3000)

                handler.page.wait_for_selector(Mapping.recurring_stop_checkbox)
                handler.page.locator(Mapping.recurring_stop_checkbox).first.click(force=True)

                handler.page.click(Mapping.approve_refund_btn, force=True)

                handler.page.wait_for_timeout(4000)

                print(f"[SUCCESS] Refund flow completed for {customer_name}")

            case _:
                print(f"[ERROR] Invalid method_type: {method_type}")