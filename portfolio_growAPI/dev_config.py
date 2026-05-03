import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

BASE_DIRECTORY: Path = Path(__file__).resolve().parent
ENVIRONMENT_PATH: Path = BASE_DIRECTORY / "dev_sensitive.env"
load_dotenv(dotenv_path=ENVIRONMENT_PATH)


class BusinessData:
    MAP: Dict[str, Dict[str, str]] = {
        "patur": {
            "userId": "sdfsdf23424",
            "name": "dev patur",
            "sms_name": "dev patur",
            "cg": "	dsfsd23424",
            "cc": "sfdsdf23424",
            "sdk": "sdfsdf23423",
            "ci": "sdfsd23424",
            "j4j5": "sdfsdf234234"
        },
        "murshe": {
            "userId": "4d644c75552349ec",
            "name": "dev murshe",
            "sms_name": "dev murshe",
            "cg": "dsfs23424",
            "cc": "sdfsdf234234",
            "sdk": "sdfsdf234234",
            "ci": "sdfsdf23424",
            "j4j5": "sdfsdf23424"
        },
        "amuta": {
            "userId": "bfadadaa0dc",
            "name": "dev amuta",
            "sms_name": "dev amuta",
            "cg": "sdfsdf2342",
            "cc": "sdfsf234234",
            "sdk": "sdffs2342",
            "ci": "sdfdsf23424",
            "j4j5": "sdfsf234234"
        },
        "shutfut": {
            "userId": "sfds23424",
            "name": "dev shutfut",
            "sms_name": "dev shutfut",
            "cg": "sdfs23424",
            "cc": "sdfdsf234234",
            "sdk": "sdfsdf234234",
            "ci": "sdfdsf234234",
            "j4j5": "sdfs23324"
        }
    }

class Url:
    api_payment: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/createPaymentProcess"
    process_info: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/getPaymentProcessInfo"
    transaction_info: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/getTransactionInfo"
    refund_info: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/refundTransaction"
    notify_url: str = "https://hook.eu1.make.celonis.com/asdasd12312312asd"
    hook_info: str = "https://hook.eu1.make.celonis.com/asdasd123123asdasd"
    glassix_email: str = "https://hook.eu1.make.celonis.com/123123asdasdasd123"
    sms_api: str = "https://api.multisend.co.il/MultiSendAPI/inbound"
    sdk_url: str = "https://www.sdk-web-test.site/?env=production&v=1.3.3"
    j4_transaction: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/settleSuspendedTransaction"
    token: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/createTransactionWithToken"
    approve_transaction: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/approveTransaction"
    recurring_refund: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/updateDirectDebit"
    invoice_url: str = "asdasd123123123asdad@hook.eu1.make.celonis.com"
    grow_website: str = "https://grow.business/"
    token_transaction: str = "https://sandbox.meshulam.co.il/api/light/server/1.0/getTokenTransactionsByExternalIdentifiers/"



class ApiConfig:
    email: str = "23434werwrwe@hook.eu1.make.celonis.com"
    apiKey: str = "sdfsdf234234"
    userid: str = "swfsdfsd234243"
    phone: str = "0500000000"
    invoiceUrl: str = "234234werwerwr@hook.eu1.make.celonis.com"

class ChargeType:
    regular: str = "1"
    j4j5: str = "2"
    token: str = "3"

class CreditInfo:
    card_number: str = os.getenv("CARD_NUMBER")
    exp_month: str = os.getenv("CARD_EXP_MONTH")
    exp_year: str = os.getenv("CARD_EXP_YEAR")
    cvv: str = os.getenv("CARD_CVV")
    card_id: str = os.getenv("CARD_ID")

class Amount:
    cc1, cc2 = "0.40", "0.50"
    cg1, cg2 = "0.20", "0.30"
    ci1, ci2 = "0.35", "0.45"
    sdk1, sdk2 = "0.45", "0.50"
    j4j5_sdk1, j4j5_sdk2 = "0.55", "0.60"
    j4j5_ci1, j4j5_ci2 = "0.80", "1.00"
    j4j5_cc1, j4j5_cc2 = "0.70", "0.90"
    j4j5_cg1, j4j5_cg2 = "0.90", "0.95"
    token_cc1, token_cc2 = "1.10", "1.20"
    token_cg1, token_cg2 = "1.25", "1.30"
    token_ci1, token_ci2 = "1.40", "1.50"
    token_sdk1, token_sdk2 = "0.65", "0.70"

class Descriptions:
    cc: str = "dev credit card business automation"
    cg: str = "dev cg business_test business automation"
    ci: str = "dev customer info business automation"
    sdk: str = "dev wallet sdk business automation"
    j4j5: str = "dev j4j5_payment  business automation"
    token: str = "dev token_payment business automation"

class Fields:
    cc1, cc2 = "dev credit card business_test automation", "working automation"
    cg1, cg2 = "dev cg business_test automation", "working automation"
    ci1, ci2 = "dev customer info automation", "working automation"
    sdk1, sdk2 = "dev sdk wallet automation", "working automation"
    j4j5_cc_1, j4j5_cc_2 = "dev j4j5_payment business regular credit card", "working automation j4j5"
    j4j5_cg_1, j4j5_cg_2 = "dev j4j5_payment business regular cg", "working automation j4j5"
    j4j5_ci_1, j4j5_ci_2 = "dev j4j5_payment business regular customer info", "working automation j4j5"
    j4j5_sdk_1, j4j5_sdk_2 = "dev j4j5_payment business regular sdk", "working automation j4j5"
    token_cc_1, token_cc_2 = "dev token_payment business regular credit card", "working automation token"
    token_cg_1, token_cg_2 = "dev token_payment business regular cg", "working automation token"
    token_ci_1, token_ci_2 = "dev token_payment business regular customer info", "working automation token"
    token_sdk_1, token_sdk_2 = "dev token_payment business regular sdk", "working automation token"

class DbConfig:
    host: str = os.getenv("DB_HOST")
    user: str = os.getenv("DB_USER")
    password: str = os.getenv("DB_PASSWORD")
    database: str = os.getenv("DB_NAME")
    port: int = int(os.getenv("DB_PORT", 3306))