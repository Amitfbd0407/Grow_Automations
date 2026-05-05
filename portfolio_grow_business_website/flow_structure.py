import os
import time
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Locator
from dotenv import load_dotenv

from biz_website.config import Mapping
from config import Url
from pathlib import Path

base_path = Path(__file__).resolve().parent
env_path = base_path / "sensitive.env"

load_dotenv(dotenv_path=env_path)


class WebAutomationHandler:
    def __init__(self, page: Page, default_iframe_selector: str = "iframe") -> None:
        self.page = page
        self.default_iframe_selector = default_iframe_selector

    def _get_element_locator(self, selector: str, use_iframe: bool) -> Locator:
        if not selector:
            raise ValueError("Selector cannot be empty.")

        if selector.startswith("label="):
            clean_label = selector.replace("label=", "")
            if use_iframe:
                return self.page.frame_locator(self.default_iframe_selector).first.get_by_label(clean_label,
                                                                                                exact=False)
            return self.page.get_by_label(clean_label, exact=False)

        if use_iframe:
            return self.page.frame_locator(self.default_iframe_selector).first.locator(selector)
        return self.page.locator(selector)

    def fill_input_field(self, selector: str, value: Any, use_iframe: bool = False) -> None:
        try:
            locator = self._get_element_locator(selector, use_iframe)
            locator.wait_for(state="visible", timeout=10000)
            locator.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            locator.fill(str(value))
        except Exception as e:
            raise Exception(f"Failed to fill field '{selector}': {e}")

    def fill_otp_boxes(self, otp_code: str) -> None:
        if not otp_code: return
        print(f"[PROCESS] Entering OTP code...")
        try:
            first_box_selector = 'input[aria-label="יש להזין את הקוד שהתקבל לנייד"]'
            self.page.wait_for_selector(first_box_selector, state="visible", timeout=15000)
            first_box = self.page.locator(first_box_selector)
            first_box.click()
            self.page.keyboard.type(str(otp_code), delay=100)
        except Exception as e:
            print(f"[ERROR] OTP insertion failed: {e}")

    def click_action_element(self, selector: str, use_iframe: bool = False) -> None:
        try:
            locator = self._get_element_locator(selector, use_iframe)
            locator.wait_for(state="visible", timeout=20000)
            locator.click(force=True)
        except Exception as e:
            raise Exception(f"Failed to click '{selector}': {e}")


    def get_text(self, selector: str, use_iframe: bool = False) -> str:
        try:
            locator = self._get_element_locator(selector, use_iframe)
            locator.wait_for(state="visible", timeout=10000)
            return locator.inner_text().strip()
        except Exception as e:
            raise Exception(f"Failed to get text from '{selector}': {e}")


    def execute_workflow_steps(self, steps: List[Dict[str, Any]]) -> None:
        for step in steps:
            action = step.get("action")
            selector = step.get("selector", "")
            value = step.get("value")
            use_iframe = step.get("iframe", False)

            match action:
                case "fill":
                    print(f"[PROCESS] Filling: {selector}")
                    self.fill_input_field(selector, value, use_iframe)
                case "click":
                    print(f"[PROCESS] Clicking: {selector}")
                    self.click_action_element(selector, use_iframe)
                case "select":
                    print(f"[PROCESS] Selecting Option: {selector} -> {value}")
                    locator = self._get_element_locator(selector, use_iframe)
                    locator.wait_for(state="attached", timeout=10000)
                    locator.select_option(value=str(value))
                case "wait":
                    duration = float(value) if value else 2.0
                    print(f"[PROCESS] Waiting {duration}s")
                    time.sleep(duration)
                case "otp":
                    self.fill_otp_boxes(str(value))
                case "verify":
                    print(f"[PROCESS] Verifying presence of: {value}")
                    if selector and value:
                        target = f"{selector} >> text={value}"
                    else:
                        target = selector if selector else f"text={value}"
                    self._get_element_locator(target, use_iframe).first.wait_for(state="visible", timeout=15000)

                case "reload":
                    print("[PROCESS] Reloading page to sync transactions...")
                    self.page.reload()


class GrowAutomationBase:

    def __init__(self, headless: bool = False):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=headless, slow_mo=400)
        self.page = self.browser.new_page()
        self.handler = WebAutomationHandler(self.page)

    def login(self):

        print(f"Opening: {Url.website}")
        self.page.goto(Url.website, timeout=60000)

        login_steps = [
            {"action": "fill", "selector": Mapping.login_business_number, "value": os.getenv("WEB_USER")},
            {"action": "fill", "selector": Mapping.login_phone_number, "value": os.getenv("WEB_PHONE")},
            {"action": "click", "selector": ".login-form_state-icon__TfouX"},
            {"action": "click", "selector": Mapping.login_connect_btn},
            {"action": "wait", "value": 3}
        ]
        self.handler.execute_workflow_steps(login_steps)

        if os.getenv("WEB_OTP"):
            self.handler.fill_otp_boxes(os.getenv("WEB_OTP"))
            time.sleep(5)

        print("Login completed.")

    def close(self):
        self.browser.close()
        self.pw.stop()


class CreditCard:
    def __init__(self, page):
        self.page = page
        self.handler = WebAutomationHandler(self.page, "iframe:visible")

        login_steps = [
            {"action": "fill", "selector": "#card-number", "value": os.getenv("CARD_NUMBER"), "iframe": True},
            {"action": "wait", "value": 1},

            {"action": "select", "selector": "#expMonth", "value": os.getenv("CARD_EXP_MONTH"), "iframe": True},

            {"action": "select", "selector": "#expYear", "value": os.getenv("CARD_EXP_YEAR")[-2:], "iframe": True},

            {"action": "fill", "selector": "#cvv", "value": os.getenv("CARD_CVV"), "iframe": True},

            {"action": "fill", "selector": "#personal-id", "value": os.getenv("CARD_ID"), "iframe": True},

            {"action": "click", "selector": "#cg-submit-btn", "iframe": True},
            {"action": "wait", "value": 3},
            {"action": "click", "selector": "#Gr0W8-confirm-btn", "iframe": False},
            {"action": "wait", "value": 2},
            {"action": "click", "selector": Mapping.back_main_page, "iframe": False},
            {"action": "wait", "value": 2}
        ]
        self.handler.execute_workflow_steps(login_steps)
        print("Credit card details filled.")