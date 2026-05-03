import json, mysql.connector, time, datetime
from dev_config import DbConfig
from dev_utils import StaticFunctions
from dev_alerts import update_status_and_check_alert

class ComparisonEngine:
    @staticmethod
    def fetch_db_data(process_id: str = None, payment_id: str = None):
        aggregated_data = {
            'card_suffix_from_logs': None,
            'asmachta_from_logs': None,
            'cField1_from_logs': None,
            'cField2_from_logs': None
        }

        if not process_id and not payment_id: return aggregated_data

        conn = None
        try:
            conn = mysql.connector.connect(host=DbConfig.host, user=DbConfig.user, password=DbConfig.password,
                                           database=DbConfig.database, port=DbConfig.port)
            cursor = conn.cursor(dictionary=True)

            if payment_id:
                cursor.execute("SELECT * FROM tb_tenants_config WHERE payment_id = %s", (payment_id,))
            else:
                cursor.execute("SELECT * FROM tb_tenants_config WHERE api_transaction_id = %s", (process_id,))

            main_rec = cursor.fetchone()
            if main_rec:
                aggregated_data.update(main_rec)
                ref_id = main_rec.get('id')
                for table, key in [("tb_tenants_config_lang", "tranID"), ("tb_payments", "payment_id"),
                                   ("tb_invoice__file_management", "payment_id")]:
                    cursor.execute(f"SELECT * FROM {table} WHERE {key} = %s", (ref_id,))
                    if row := cursor.fetchone(): aggregated_data.update(row)

            cursor.execute("SELECT * FROM tb_light_api__payment_logs WHERE process_id = %s ORDER BY id DESC",
                           (process_id if process_id else main_rec.get('api_transaction_id'),))

            for log in cursor.fetchall():
                for field_name in ['comments', 'response']:
                    content = log.get(field_name)
                    if content and isinstance(content, str) and ('{' in content):
                        try:
                            p = json.loads(content)
                            inner = p.get('data', p)
                            if isinstance(inner, str): inner = json.loads(inner)

                            if isinstance(inner, dict):
                                if not aggregated_data.get('card_suffix_from_logs'):
                                    if inner.get('cardSuffix'):
                                        aggregated_data['card_suffix_from_logs'] = inner.get('cardSuffix')
                                        aggregated_data['asmachta_from_logs'] = inner.get('asmachta')
                                        aggregated_data['card_brand_from_logs'] = inner.get('cardBrand')
                                        aggregated_data['card_exp_from_logs'] = inner.get('cardExp')

                                cField = inner.get('customField') or inner.get('customFields') or inner
                                if isinstance(cField, dict):
                                    if cField.get('cField1') and not aggregated_data.get('cField1_from_logs'):
                                        aggregated_data['cField1_from_logs'] = cField.get('cField1')
                                    if cField.get('cField2') and not aggregated_data.get('cField2_from_logs'):
                                        aggregated_data['cField2_from_logs'] = cField.get('cField2')
                        except:
                            pass

                if aggregated_data.get('card_suffix_from_logs') and aggregated_data.get('cField1_from_logs'):
                    break
        except:
            pass
        finally:
            if conn and conn.is_connected(): conn.close()
        return aggregated_data


def run_full_audit(bot):
    time.sleep(5)
    print(f"[Run ID: {bot.run_id}] Starting Audit Comparison...")

    db_map = ComparisonEngine.fetch_db_data(bot.process_id)
    payload_map = bot.request_payload


    approve_res_full = bot.approve_response or {}
    a_data = approve_res_full.get('data', {})

    if isinstance(a_data, dict) and 'transactions' in a_data:
        a_root = a_data['transactions'][-1]
    elif isinstance(a_data, dict):
        a_root = a_data
    else:
        a_root = {}

    sync_data_full = bot.sync_data or {}
    sync_root = sync_data_full.get('data', {}) if isinstance(sync_data_full.get('data'), dict) else {}
    sync_txs = sync_root.get('transactions', []) if isinstance(sync_root, dict) else []
    s_tx = sync_txs[-1] if sync_txs else {}
    sync_custom = sync_root.get('customField', {}) if isinstance(sync_root, dict) else {}

    tx_info_full = bot.transaction_data or {}
    t_root = tx_info_full.get('data', tx_info_full) if isinstance(tx_info_full.get('data'),
                                                                  (dict, list)) else tx_info_full
    if not isinstance(t_root, dict): t_root = {}
    t_custom = t_root.get('customField', {})

    print("\n" + "=" * 60)
    print("DEBUG: ALL DATA SOURCES (PRETTY VIEW)")
    sources = [
        ("PAYLOAD", payload_map),
        ("DATABASE", db_map),
        ("PROCESS_INFO", sync_data_full),
        ("TRANSACTION_INFO", tx_info_full),
        ("APPROVE_RES", approve_res_full)
    ]
    for name, data in sources:
        print(f"\n>>> {name}:")
        if data:
            print(json.dumps(data, indent=4, ensure_ascii=False, default=str))
        else:
            print("{}")
    print("\n" + "=" * 60 + "\n")

    db_full_name = f"{db_map.get('payer_first_name', '')} {db_map.get('payer_last_name', '')}".strip()
    is_recurring = str(payload_map.get("paymentType")) == "1"
    db_single_sum = float(db_map.get('payment_sum', 0) or 0)
    db_num_payments = int(db_map.get('all_payments_num', 1) or 1)
    db_total_calculated_sum = db_single_sum if is_recurring else (db_single_sum * db_num_payments)
    db_date_raw = db_map.get('payment_date')
    db_date_formatted = datetime.datetime.fromtimestamp(db_date_raw).strftime('%d/%m/%y') if isinstance(db_date_raw,
                                                                                                        (int,
                                                                                                         float)) else db_date_raw


    audit_items = [
        ("ProcessID", "N/A", db_map.get("api_transaction_id"), sync_root.get("processId"), t_root.get("processId"),
         a_root.get("processId")),
        ("TransID", "N/A", db_map.get("payment_id"), s_tx.get("transactionId"), t_root.get("transactionId"),
         a_root.get("transactionId")),
        ("Sum", payload_map.get("sum"), db_total_calculated_sum, s_tx.get("sum"), t_root.get("sum"), a_root.get("sum")),
        ("Status", "N/A", db_map.get("status"), s_tx.get("statusCode"), t_root.get("statusCode"),
         a_root.get("statusCode")),
        ("Date", "N/A", db_date_formatted, s_tx.get("paymentDate"), t_root.get("paymentDate"),
         a_root.get("paymentDate")),
        ("FullName", payload_map.get("pageField[fullName]"), db_full_name, s_tx.get("fullName"), t_root.get("fullName"),
         a_root.get("fullName")),
        ("Phone", payload_map.get("pageField[phone]"), db_map.get("payer_phone"), s_tx.get("payerPhone"),
         t_root.get("payerPhone"), a_root.get("payerPhone")),
        ("Email", payload_map.get("pageField[email]"), db_map.get("payer_email"), s_tx.get("payerEmail"),
         t_root.get("payerEmail"), a_root.get("payerEmail")),
        ("Asmachta", "N/A", db_map.get("asmachta_from_logs"), s_tx.get("asmachta"), t_root.get("asmachta"),
         a_root.get("asmachta")),
        ("CardBrand", "N/A", db_map.get("card_brand_from_logs"), s_tx.get("cardBrand"), t_root.get("cardBrand"),
         a_root.get("cardBrand")),
        ("cField1", payload_map.get("cField1"), db_map.get('cField1_from_logs'), sync_custom.get("cField1"),
         t_custom.get("cField1"), "N/A"),
        ("cField2", payload_map.get("cField2"), db_map.get('cField2_from_logs'), sync_custom.get("cField2"),
         t_custom.get("cField2"), "N/A"),
        ("Payments", payload_map.get("paymentNum") or payload_map.get("allPaymentsNum"), db_map.get("all_payments_num"),
         s_tx.get("allPaymentsNum"), t_root.get("allPaymentsNum"), a_root.get("allPaymentsNum")),
    ]

    source_errors = {"Payload": [], "DB": [], "PROCESS INFO": [], "TRANSACTION INFO": [], "APPROVE RES": []}


    print(
        f"| {'Label':<13} | {'Payload':<10} | {'DB':<10} | {'PROCESS':<8} | {'TX INFO':<8} | {'APPROVE':<8} | {'Stat':<4} |")
    print("-" * 110)

    for label, pin, db, syn, txi, apr in audit_items:
        is_amt = label in ["Sum"]
        v_p, v_d, v_s, v_t, v_a = [StaticFunctions.normalize(x, is_amt) for x in [pin, db, syn, txi, apr]]

        val_map = {"Payload": v_p, "DB": v_d, "Sync": v_s, "TxInfo": v_t, "Approve": v_a}
        clean_vals = {k: v for k, v in val_map.items() if v not in ["", "N/A"]}

        status = "PASS"

        if label == "Payments" and is_recurring:
            if v_p == v_d and v_s == v_t == "1":
                status = "PASS"
            else:
                status = "FAIL"

        elif len(set(clean_vals.values())) > 1:
            status = "FAIL"

        if status == "FAIL":
            valid_list = list(clean_vals.values())

            consensus = max(set(valid_list), key=valid_list.count)
            if v_p not in ["", "N/A"] and v_p != consensus: source_errors["Payload"].append(label)
            if v_d not in ["", "N/A"] and v_d != consensus: source_errors["DB"].append(label)
            if v_s not in ["", "N/A"] and v_s != consensus: source_errors["PROCESS INFO"].append(label)
            if v_t not in ["", "N/A"] and v_t != consensus: source_errors["TRANSACTION INFO"].append(label)
            if v_a not in ["", "N/A"] and v_a != consensus: source_errors["APPROVE RES"].append(label)

        print(
            f"| {label:<13} | {v_p[:10]:<10} | {v_d[:10]:<10} | {v_s[:8]:<8} | {v_t[:8]:<8} | {v_a[:8]:<8} | {status:<4} |")

class SettlementAudit:
    @staticmethod
    def run(bot):

        approve_raw = bot.approve_response
        data_node = approve_raw.get('data', {})
        if isinstance(data_node, dict) and 'transactions' in data_node:
            approve_data = data_node['transactions'][-1]
        else:
            approve_data = data_node

        if not isinstance(approve_data, dict):
            approve_data = {}

        new_tid = approve_data.get("transactionId")

        db_log_record = None
        conn = None
        try:
            conn = mysql.connector.connect(
                host=DbConfig.host, user=DbConfig.user, password=DbConfig.password,
                database=DbConfig.database, port=DbConfig.port
            )
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM tb_light_api__payment_logs WHERE payment_id = %s LIMIT 1"
            cursor.execute(query, (new_tid,))
            db_log_record = cursor.fetchone()
        except Exception as e:
            print(f"DEBUG: SQL Error - {e}")
        finally:
            if conn: conn.close()

        db_inner_data = {}
        if db_log_record:
            if db_log_record.get('response'):
                try:
                    r_parsed = json.loads(db_log_record['response'])
                    if isinstance(r_parsed, dict):
                        db_inner_data.update(
                            r_parsed.get('data', r_parsed) if isinstance(r_parsed.get('data'), dict) else r_parsed)
                except:
                    pass

            if db_log_record.get('comments'):
                try:
                    c_parsed = json.loads(db_log_record['comments'])
                    if isinstance(c_parsed, dict) and 'cardToken' in c_parsed and not db_inner_data.get('cardToken'):
                        db_inner_data['cardToken'] = c_parsed['cardToken']
                except:
                    pass

        print("\n" + "=" * 60)
        print("DEBUG: ALL DATA SOURCES (PRETTY VIEW)")

        sources = [
            ("PAYLOAD", bot.approve_payload),
            ("APPROVE_RES", bot.approve_response),
            ("DATABASE_LOG", db_log_record)
        ]

        for name, data in sources:
            print(f"\n>>> {name}:")
            if data:
                print(json.dumps(data, indent=4, ensure_ascii=False, default=str))
            else:
                print("{}")
        print("\n" + "=" * 60 + "\n")

        payload = bot.request_payload
        card_token_sent = bot.sync_data.get('data', {}).get('transactions', [{}])[-1].get(
            'cardToken') or bot.sync_data.get('data', {}).get('cardToken') if isinstance(bot.sync_data, dict) else "N/A"

        items = [
            ("TransID", bot.approve_payload.get("transactionId") if isinstance(bot.approve_payload, dict) else "N/A",
             approve_data.get("transactionId"), db_inner_data.get("transactionId")),
            ("Sum", payload.get("sum") if isinstance(payload, dict) else "N/A", approve_data.get("sum"),
             db_inner_data.get("sum")),
            ("Status", "N/A", approve_data.get("statusCode"), db_inner_data.get("statusCode")),
            ("Asmachta", bot.approve_payload.get("asmachta") if isinstance(bot.approve_payload, dict) else "N/A",
             approve_data.get("asmachta"), db_inner_data.get("asmachta")),
            ("CardToken", card_token_sent or "N/A", approve_data.get("cardToken"), db_inner_data.get("cardToken")),
            ("TransToken", "N/A", approve_data.get("transactionToken"), db_inner_data.get("transactionToken")),
            ("CardSuffix", "N/A", approve_data.get("cardSuffix"), db_inner_data.get("cardSuffix")),
            ("CardBrand", "N/A", approve_data.get("cardBrand"), db_inner_data.get("cardBrand")),
        ]

        print(f"| {'Label':<12} | {'Payload':<18} | {'Approve (API)':<20} | {'DB (Log Res)':<20} | {'Stat':<4} |")
        print("-" * 90)

        errors = []
        for label, p_val, a_val, d_val in items:
            is_amt = (label == "Sum")
            v_p = StaticFunctions.normalize(p_val, is_amt)
            v_a = StaticFunctions.normalize(a_val, is_amt)
            v_d = StaticFunctions.normalize(d_val, is_amt)

            if v_a == v_d and v_a != "":
                if v_p not in ["", "N/A"] and v_p != v_a:
                    status = "FAIL"
                    errors.append(f"Payload mismatch: {label}")
                else:
                    status = "PASS"
            else:
                if label in ["CardBrand", "CardSuffix"] and v_d == "":
                    status = "PASS"
                else:
                    status = "FAIL"
                    errors.append(f"API/DB mismatch: {label}")

            print(f"| {label:<12} | {v_p[:18]:<18} | {v_a[:20]:<20} | {v_d[:20]:<20} | {status:<4} |")

        print("=" * 90 + "\n")

        if errors:
            reason_msg = " | ".join(errors)
            update_status_and_check_alert(bot, status="FAIL", step="Final Settlement Audit", reason=reason_msg)
            raise Exception(f"Settlement Audit Failed: {reason_msg}")

        print(f"[Run ID: {bot.run_id}] Settlement Audit Passed.")
        return True