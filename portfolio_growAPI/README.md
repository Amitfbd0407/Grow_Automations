Payment Integration & Automated Audit System
A robust, production-ready Python framework designed for automated payment processing, end-to-end testing, and real-time transaction auditing. This system integrates API communication, UI automation (Playwright), and database verification to ensure 100% financial data integrity.

Key Features
End-to-End Payment Flow: Automates the full lifecycle of a transaction—from initial Auth requests to UI credit card injection and final settlement.
Multi-Source Audit Engine: A sophisticated comparison logic that cross-references data between API Responses, Database Logs, and UI State to detect discrepancies in real-time.
Dynamic UI Automation: Utilizes Playwright to handle complex iframe-based payment forms, including smart waiting and error detection.
Automated Alerting System: Integrated with PostgreSQL for status tracking and Make.com (Integromat) webhooks for instant failure notifications via Email/SMS.
Extensible Bot Architecture: Built with an Object-Oriented approach (BasePaymentBot), allowing easy support for different payment types (Regular, J4/J5, Token-based, Recurring).
Security First: Designed with strict separation of configuration and sensitive data using environment variables (python-dotenv).

Tech Stack
Language: Python 3.10+
Automation: Playwright (Chromium)
API/Networking: Requests, REST APIs
Databases: MySQL (Transactional logs), PostgreSQL (Automation health monitoring)
Integrations: Make.com Webhooks, SMS Gateways
Utility: File Locking (Concurrency control), UUIDs, ZoneInfo

System Architecture
Request Layer: The bot initiates a payment process via the Meshulam/Grow API.
UI Interaction: Playwright navigates to the generated payment URL, handles the iframe, and executes the transaction.
Sync & Verify: The system fetches the transaction data via API and queries the internal MySQL database.
Audit: The ComparisonEngine ensures that the sum, currency, token, and customer details match across all layers.
Alert: Any mismatch or technical failure triggers a database update and a high-priority alert webhook.

Setup & Installation

Clone the repository:
code
Bash
git clone https://github.com/Amitfbd0407/GrowAPI.git
Install dependencies:
code
Bash
pip install -r requirements.txt
playwright install chromium
Configuration:
Create a .env file based on the provided logic to store your API keys and Database credentials.

💡 Note
This repository is a sanitized version of a production system, provided for portfolio purposes. Sensitive URLs, API keys, and private business logic have been removed or replaced with placeholders.
