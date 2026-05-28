# Grow Payments Automation Framework

This is an End-to-End (E2E) automation framework built with Python to test core payment workflows, API configurations, and database integrity for Grow Payments.

---

## 📁 Repository Structure

All major testing folders in this project (`dev_regular`, `dev_token`, and `j4j5` folders) share the exact same internal architecture, split into 4 core modules:

* **`cg/`** - Clearing Gateway integration and processing tests.
* **`credit_card/`** - Credit Card UI flows, billing validation, and secure iFrame components.
* **`customer_info/`** - User onboarding, metadata, and client profile verification.
* **`sdk_wallet/`** - Digital wallet functionality, balances, and core SDK endpoints.

### Key Infrastructure Files:
* **`j4j5_cg_run_all.py`** - The main test runner to execute the entire suite.
* **`dev_compare_hook_db.py`** - Database Hook that connects to PostgreSQL for real-time data validation.
* **`dev_alerts.py`** - Automated verification for real-time SMS alerts and Email invoices.
* **`portfolio_grow_business_website/`** - Web UI checkout tests for the main storefront.

---

## 🔧 Installation & Setup

### 1. Clone the repository:
```bash
git clone [https://github.com/](https://github.com/)[Amitfbd0407]/[Grow_automations].git
cd Grow_automations
