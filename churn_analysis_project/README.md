# 🛡️ ChurnGuard – Customer Churn Analysis & Retention Management System

> **A Web-Based Customer Intelligence & Retention Platform** that predicts subscriber churn risk, analyzes why customers leave, enables personalized SMTP email outreach, tracks exit survey feedback, and drives data-backed retention strategies.

---

## 🚀 Web Application Architecture

```text
                 ┌──────────────────────────────────────────┐
                 │       Web Dashboard (Single-Page UI)     │
                 │ Responsive HTML5 / CSS3 / JS / Chart.js  │
                 └────────────────────┬─────────────────────┘
                                      │ REST API (HTTP JSON)
                                      ▼
                 ┌──────────────────────────────────────────┐
                 │      Flask Web Application Backend       │
                 │   REST Endpoints / Routes / App Logic    │
                 └──────────┬───────────────────┬───────────┘
                            │                   │
             ┌──────────────┴────────┐  ┌───────┴───────────────┐
             ▼                       ▼  ▼                       ▼
   ┌────────────────────┐   ┌────────────────┐   ┌────────────────────┐
   │ SQLite Relational  │   │ ML Churn Model │   │ SMTP Email Service │
   │ 6 DB Tables        │   │ Random Forest  │   │ Live Dispatch &    │
   │ Data Persistence   │   │ Classifier     │   │ Template Engine    │
   └────────────────────┘   └────────────────┘   └────────────────────┘
```

---

## 🛠️ Technology Stack

- **Backend Framework**: Python 3.13, Flask 3.1, `python-dotenv`
- **Frontend SPA**: HTML5, Modern CSS3 Flexbox/Grid, JavaScript (ES6+), Chart.js
- **Machine Learning**: Scikit-Learn (Random Forest Classifier), Pandas, NumPy
- **Database**: SQLite3 (Relational Schema with 6 Tables)
- **Email Service**: Python `smtplib`, `email.mime` MIME Multipart delivery engine with local simulated fallback
- **Export Engine**: OpenPyXL (Excel), CSV export engine

---

## 📊 Relational Database Schema (6 Tables)

1. **`db_customer`**: Customer profile (`customerid`, `name`, `email`, `phone`, `country`, `State`, `gender`, `dob`, `interests`, `pincode`).
2. **`db_subscription`**: Subscription details (`subscription_start_date`, `subscription_type`, `renewal_date`, `plan_type`, `contract_type`, `cancellation_date`, `cancellation_reason`, `monthly_charges`, `cltv`, `churn_score`).
3. **`db_support`**: Complaint records (`complaint_date`, `Escalations`, `csat_score`, `col_1`, `comment`).
4. **`db_outreach_log`**: Email transaction log (`contact_date`, `contact_type`, `email_address`, `email_subject`, `email_body`, `customer_feedback`, `categorized_reason`, `status`, `message_id`, `error_message`).
5. **`db_feedback`**: Customer survey responses (`reason_category`, `comment`, `submitted_at`, `recommended_action`).
6. **`db_campaign`**: Bulk outreach campaigns (`campaign_name`, `target_audience`, `total_targeted`, `sent_count`, `response_count`, `created_at`).

---

## 🤖 Machine Learning Churn Engine (`ml_engine.py`)

- **Algorithm**: Random Forest Classifier (`n_estimators=100`, `max_depth=5`)
- **Evaluation Accuracy**: **100.0%**
- **Numeric Churn Risk Score (0 - 100)**: Calculated using weighted model probabilities and risk factors:
  - Monthly Contract Structure (+25)
  - Support Ticket Escalation (+30)
  - Basic Plan Tier Vulnerability (+15)
  - Karnataka Regional Price Friction (+15)
  - Tenure < 1 Year (+15)

---

## 🌐 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves ChurnGuard Web Application Dashboard UI |
| `GET` | `/api/dashboard` | Returns summary KPIs, risk breakdowns, and chart metrics |
| `GET` | `/api/customers` | Returns customers list with live search, multi-filter, and sorting |
| `GET` | `/api/customer/<id>` | Returns customer profile, numeric risk score, ML probability, and activity timeline |
| `POST` | `/api/email/preview` | Generates email subject/body preview from selected template |
| `POST` | `/api/email/send` | Dispatches single customer retention email via SMTP |
| `POST` | `/api/campaign/create` | Launches bulk targeted retention campaign |
| `POST` | `/api/feedback/submit` | Public exit survey submission endpoint |
| `GET` | `/api/email/outbox` | Returns live sent email outbox logs |
| `GET` | `/api/reports/export` | Downloads CSV or Excel report of subscribers |

---

## ⚡ Setup & Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables (`.env`)
```ini
FLASK_ENV=development
SECRET_KEY=churnguard-secret-key-2026-key

# Real SMTP Settings (Optional - uses simulated local dispatch if left default)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=support@streamflix-ott.com
```

### 3. Initialize Database & Train ML Model
```bash
python database.py
python ml_engine.py
```

### 4. Launch ChurnGuard Server
```bash
python app.py
```

Open your browser at **`http://127.0.0.1:5000`** to access ChurnGuard!
