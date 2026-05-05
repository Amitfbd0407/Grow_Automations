import os
from dotenv import load_dotenv
from pathlib import Path

base_path = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_path / "sensitive.env")


class Db:
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "your_database_name")
    DB_PORT = int(os.getenv("DB_PORT", 3306))



class Url:
    website = "https://grow.website/"
    glassix_email: str = "https://hook.eu1.make.celonis.com/65r7w250fpdg94sixaolorjsuh51yymp"



class Mapping:
    new_transaction= "עסקה חדשה"
    regular_payment=  "מוצג: רגיל"
    write_amount = "לפי סכום"
    temporary_customer = "לקוח מזדמן"
    full_name = "label=שם מלא (חובה)"
    phone = "label=טלפון (חובה)"
    input_email = "input[name='emailAddress']"
    payment_number = "label=מספר תשלומים"
    credit_card = "text=כרטיס אשראי"
    identity_card = "תעודת זהות"
    login_business_number = "label=מספר חשבון ב-Grow"
    login_phone_number = "label=מספר טלפון"
    login_connect_btn = "label=התחברות"
    back_main_page = "text=חזרה לעמוד הראשי"
    transaction_page = 'a:has-text("עסקאות")'
    recurring_menu_link = 'a[href="/recurring-debits"]'
    refund_btn = "text=ביצוע זיכוי"
    approve_refund_btn = "text=אישור וזיכוי"
    thank_you_btn = "text=תודה"
    recurring_payment = "הוראת קבע"
    recurring_number_dropdown = '[aria-label*="מספר החיובים החודשיים"]'
    recurring_number_option_12 = 'role=option >> text="12"'
    inside_stop_recurring_btn = "span.top-actions_button-text__Q3_we:has-text('עצירת הו״ק')"
    confirm_stop_btn = "span.action-prompt_button-text__agXz_:has-text('כן, עצירה')"
    recurring_stop_checkbox = ".checkbox_state-icon__w7fZr"





