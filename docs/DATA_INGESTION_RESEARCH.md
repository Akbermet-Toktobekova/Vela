# Technical Research & Architecture: Automated Financial Data Ingestion

**Project:** Vela — Multi-Agent Personal Financial Advisor (BSc Computer Science Thesis)  
**Author:** Akbermet Toktobekova  
**Topic:** Real-Time NFC Tap-to-Pay Ingestion, Notification Parsing, and Open Banking (PSD2) Synchronization  

---

## 1. Executive Summary & Problem Formulation

### 1.1 The Failure of Manual Expense Tracking
Traditional personal finance apps suffer from an estimated **70–85% user drop-off within 30 days**. The primary friction point is **manual logging** (requiring the user to remember and input every coffee, grocery run, or transit ticket). When data is incomplete, downstream AI advisory and optimization engines become inaccurate or obsolete.

### 1.2 The Paradigm Shift: Automated Multi-Source Ingestion
For an autonomous multi-agent advisor to deliver proactive guidance, it requires a continuous, high-fidelity stream of transactional data. This research outlines the technical mechanisms for ingesting:
1. **On-Device NFC Tap-to-Pay / Wallet Purchases** (Instantaneous at point of sale).
2. **Bank Account & Transfer Synchronization** (Card purchases, salary deposits, P2P transfers via Open Banking PSD2).
3. **Receipt & Notification Streams** (Optical Character Recognition and push notification interception).

```
                      ┌────────────────────────────────────────┐
                      │        DATA SOURCES (Point of Sale)    │
                      └────────────────────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
   ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
   │  Apple Pay /  │         │ Android Push  │         │ Open Banking  │
   │  FinanceKit / │         │ Notifications │         │  PSD2 APIs    │
   │   Shortcuts   │         │    & SMS      │         │ (GoCardless)  │
   └───────────────┘         └───────────────┘         └───────────────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     ▼
                      ┌────────────────────────────────────────┐
                      │   VELA DATA INGESTION & ENRICHMENT     │
                      │  • Merchant Normalizer                 │
                      │  • ISO 18245 MCC & 50/30/20 Tagging    │
                      │  • Anomaly & Velocity Detector         │
                      └────────────────────────────────────────┘
                                     │
                                     ▼
                      ┌────────────────────────────────────────┐
                      │   MULTI-AGENT REASONING (CrewAI)       │
                      │   Coordinator ➔ Budget ➔ Debt ➔ Savings│
                      └────────────────────────────────────────┘
```

---

## 2. Channel 1: On-Device Tap-to-Pay & Phone Purchase Ingestion

Capturing purchases at the exact moment the phone taps an NFC terminal or executes an in-app payment requires platform-specific architectural patterns.

### 2.1 Apple Ecosystem (iOS)

Apple sandboxes financial data for privacy reasons, restricting direct read access to the Secure Element. However, three compliant integration paths exist:

#### A. Apple FinanceKit API (`iOS 17.4+`)
* **Overview:** Apple introduced `FinanceKit` and `FinanceKitUI` to provide financial management apps with secure, user-consented access to Apple Card, Apple Cash, and linked financial accounts.
* **Core Structures:**
  * `Transaction`: Exposes `id`, `transactionAmount`, `transactionDate`, `status` (`authorized`, `posted`, `pending`), `merchantName`, `merchantCategoryCode` (ISO 18245), and `creditDebitIndicator`.
  * `TransactionHistory`: Supports asynchronous polling and long-running queries via `transactionHistory(forAccountID:since:isMonitoring:)`.
* **Requirements:** Entitlement request from Apple Developer Portal under the "Finance" App Store category.

#### B. Apple Shortcuts Automation Webhook (Immediate Real-World Solution)
* **Architecture:** iOS allows users to create personal automations triggered by:
  `Automation ➔ "When any transaction is made with Apple Pay"`
* **Payload Forwarding:** The automation extracts `Transaction Amount`, `Merchant Name`, and `Card Name`, and immediately fires a background HTTP POST request to Vela's Ingestion Webhook:
  ```http
  POST https://api.vela-advisor.com/api/ingestion/webhook/apple-pay
  Content-Type: application/json
  Authorization: Bearer <user_device_token>

  {
    "source": "apple_pay",
    "amount": 14.50,
    "currency": "EUR",
    "raw_merchant": "SPAR CORVIN BUDAPEST",
    "timestamp": "2026-08-24T07:15:00Z"
  }
  ```
* **Advantage:** Works in real time without needing specialized Apple enterprise entitlements.

---

### 2.2 Android Ecosystem

Android provides accessible OS-level hooks for intercepting financial events in real time.

#### A. `NotificationListenerService`
* **Mechanism:** Extending `NotificationListenerService` grants the application permission to listen to `onNotificationPosted(StatusBarNotification sbn)`.
* **Filtering & Security:**
  1. Filter incoming notifications by package name (e.g., `com.revolut.revolut`, `hu.otpbank.smartbank`, `com.wise`, `com.google.android.apps.walletnfcrel`).
  2. Extract notification title and body text (e.g., *"Paid €8.50 at Costa Coffee"*).
  3. Discard any messages containing OTPs, 2FA tokens, or security codes before transmission.

#### B. `BroadcastReceiver` (`SMS_RECEIVED`)
* **Mechanism:** Transactional SMS sent by traditional banking institutions are intercepted via `android.provider.Telephony.SMS_RECEIVED`.
* **Regex / Pattern Matching:** Extracts amount, currency, balance residue, and merchant name via templated regex rules.

---

## 3. Channel 2: Open Banking (PSD2) Synchronization

In the European Union, the **Payment Services Directive 2 (PSD2)** mandates that financial institutions expose secure, standardized APIs for **Account Information Service Providers (AISP)**.

### 3.1 Aggregator Comparison

| Provider | Regional Coverage | Supported Banks | Developer Access & Pricing | Best Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **GoCardless (Nordigen)** | 🇪🇺 EU / UK (2,500+ banks) | OTP Bank, Erste, K&H, Revolut, Wise, Raiffeisen | **Free Open Banking API Tier** for building & testing | **Primary choice for EU / Hungarian Banks** |
| **Plaid** | 🇺🇸 US / 🇬🇧 UK / 🇪🇺 EU | Major global banks | Robust Sandbox with pre-configured mock institutions | Ideal for instant simulation & sandbox testing |
| **Tink / Salt Edge** | 🇪🇺 EU / Global | Comprehensive EU coverage | Enterprise pricing tier | Production scaling |

### 3.2 Open Banking Data Model

Once a bank is linked via OAuth2 consent, the API yields structured financial objects:

```json
{
  "transaction_id": "tx_984310924",
  "booking_date": "2026-08-23",
  "value_date": "2026-08-23T14:22:00Z",
  "amount": -42.50,
  "currency": "EUR",
  "remittance_information_unstructured": "POS 4123 TESCO EXPRESS BUDAPEST",
  "merchant_name": "Tesco",
  "merchant_category_code": "5411",
  "proprietary_bank_transaction_code": "CARD_PAYMENT",
  "balance_after_transaction": 2341.80
}
```

---

## 4. Ingestion Pipeline & AI Enrichment Engine

Raw data from bank feeds and tap-to-pay triggers is typically unstructured. Vela applies a 3-stage enrichment pipeline:

```
[ Raw Ingestion ] ➔ [ 1. Merchant Normalization ] ➔ [ 2. 50/30/20 Tagging ] ➔ [ 3. Multi-Agent Triggers ]
```

### 4.1 Stage 1: Merchant Normalization & Deduplication
* **Input:** `"POS 0923 STARBUCKS #102 HU"`
* **Clean Name:** `"Starbucks"`
* **Category:** `"Dining & Coffee"` (ISO MCC 5814)
* **Deduplication:** Matching pending NFC webhook events against posted Open Banking ledger entries using timestamp proximity (±3 minutes) and amount matching.

### 4.2 Stage 2: 50/30/20 Framework & Discretionary Tagging
* Essential (Needs: 50%): Supermarkets, utilities, public transit, pharmacy.
* Discretionary (Wants: 30%): Coffee shops, restaurant dining, fast fashion, streaming services.
* Savings / Liabilities (20%): Loan amortizations, transfer to brokerage or HYSA accounts.

### 4.3 Stage 3: Autonomous Agent Triggers
* **Velocity Anomaly:** If 3 wants-based purchases occur within 2 hours ➔ `Budget Specialist` delivers gentle, actionable notification.
* **Salary / Inflow Detection:** When a credit transaction matching income patterns lands ➔ `Savings Coach` prepares a 1-tap automated allocation proposal.
* **High-Interest Liability Accrual:** When credit card balance increases ➔ `Debt Optimizer` recalculates payoff timelines.

---

## 5. Technical Implementation Roadmap for Vela Prototype

| Module | Component | Description |
| :--- | :--- | :--- |
| **Backend Ingestion Service** | `backend/services/ingestion.py` | Receives raw transaction events from Webhooks, Open Banking mocks, and NFC listeners. |
| **Normalizer & Rule Engine** | `backend/services/normalizer.py` | Cleans merchant strings, assigns MCC codes, and computes 50/30/20 bucket allocation. |
| **Bank Sync API** | `backend/api/routes_ingestion.py` | Endpoints for linking simulated/real bank institutions and polling live transactions. |
| **Mobile Bank & Sync Hub** | `mobile/src/screens/BankingSyncScreen.tsx` | UI for linking Revolut, OTP, Wise, Apple Pay, and viewing real-time transaction streams. |
| **Instant NFC Simulator** | `mobile/src/components/NfcSimulatorModal.tsx` | Interactive point-of-sale simulator allowing the examiner to trigger instant tap purchases. |

---

*Document created for inclusion in the Thesis Research & System Architecture portfolio.*
