import time
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Locator


class Fields_and_clicks:
    def __init__(self, page: Page, iframe_selector: str) -> None:
        self.page, self.iframe_selector = page, iframe_selector

    def get_target(self, selector: str, inside_iframe: bool) -> Locator:
        if inside_iframe:
            try:
                self.page.wait_for_selector(self.iframe_selector, state="attached", timeout=15000)
                return self.page.frame_locator(self.iframe_selector).first.locator(selector)
            except Exception:
                raise Exception(f'frame ("{self.iframe_selector}") not found')
        return self.page.locator(selector)

    def click(self, selector: str, inside_iframe: bool = True) -> None:
        try:
            target_locator: Locator = self.get_target(selector, inside_iframe)
            target_locator.wait_for(state="visible", timeout=15000)
            target_locator.hover()
            time.sleep(1)
            target_locator.click(force=True)
        except Exception:
            raise Exception(f'click ("{selector}") not found')

    def fillFields(self, selector: str, value: Any, inside_iframe: bool = True) -> None:
        if value is None: return
        try:
            target_locator: Locator = self.get_target(selector, inside_iframe)
            target_locator.wait_for(state="visible", timeout=10000)
            target_locator.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            target_locator.fill(str(value))
        except Exception:
            raise Exception(f'field ("{selector}") not found')

    def run_custom_steps(self, steps: Optional[List[Dict[str, Any]]] = None) -> None:
        if not steps: return
        for s in steps:
            at, sel, ifr, val = s.get("action", ""), s.get("selector", ""), s.get("iframe", True), s.get("value")

            match at:
                case "click":
                    self.click(sel, ifr)
                case "fill":
                    self.fillFields(sel, val, ifr)
                case "select":
                    self.get_target(sel, ifr).select_option(value=str(val))
                case "wait":
                    time.sleep(float(val) if val else 2)

    @staticmethod
    def run(url: str, credit_info: Any, bot, pre_steps: Optional[List[Dict[str, Any]]] = None) -> None:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, slow_mo=500)
            context = browser.new_context()
            page = context.new_page()
            try:
                bot.current_step = "Navigate to URL"
                try:
                    page.goto(url, timeout=60000)
                except Exception:
                    raise Exception("Unable to open URL")

                handler = Fields_and_clicks(page, ".js-cg-iframe, iframe[src*='meshulam'], #int_payment_frame, iframe")

                bot.current_step = "Pre-steps"
                handler.run_custom_steps(pre_steps)

                bot.current_step = "Fill Card"
                handler.fillFields("#card-number", credit_info.card_number)
                handler.get_target("#expMonth", True).select_option(str(credit_info.exp_month))
                handler.get_target("#expYear", True).select_option(str(credit_info.exp_year))
                #handler.fillFields("#cvv", credit_info.cvv)

                bot.current_step = "Fill ID"
                p_id = handler.get_target("#personal-id", True)
                if p_id.is_visible(timeout=3000):
                    handler.fillFields("#personal-id", credit_info.card_id)


                bot.current_step = "Submit Click"
                handler.click("#cg-submit-btn")

                # Verify Payment Status
                bot.current_step = "Verify UI Success"
                time.sleep(5)

                # Check 1: Explicit Error Messages
                error_selectors = ["#cg-error-msg", ".error-message", ".validation-error", ".text-danger"]
                for sel in error_selectors:
                    try:
                        err_el = handler.get_target(sel, True)
                        if err_el.is_visible(timeout=500):
                            msg = err_el.inner_text().strip()
                            if msg: raise Exception(f"Card rejected on payment page: {msg}")
                    except Exception as e:
                        if "rejected" in str(e): raise e
                        continue

                # Check 2: Check if form is still visible
                try:
                    card_field = handler.get_target("#card-number", True)
                    if card_field.is_visible(timeout=2000):
                        raise Exception("Payment failed: Form still visible (invalid card data)")
                except Exception as e:
                    if "failed" in str(e): raise e

                bot.current_step = "Processing Payment"
                time.sleep(10)

            finally:
                context.close()
                browser.close()