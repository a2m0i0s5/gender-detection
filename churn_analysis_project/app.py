import os
import sqlite3
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file, Response
from datetime import datetime
import io

from database import DB_NAME, get_db_connection, init_db
from ml_engine import predictor
from email_service import send_customer_email, EMAIL_TEMPLATES, generate_template_email

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "churnguard-secret-key-2026")

# Train ML Model on startup
predictor.train()

@app.route('/')
def index():
    return render_template('index.html')

# API 1: Dashboard Summary KPIs & Visual Metrics
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_metrics():
    conn = get_db_connection()
    df_sub = pd.read_sql_query("SELECT * FROM db_subscription", conn)
    df_cust = pd.read_sql_query("SELECT * FROM db_customer", conn)
    df_sup = pd.read_sql_query("SELECT * FROM db_support", conn)
    df_out = pd.read_sql_query("SELECT * FROM db_outreach_log", conn)
    df_feed = pd.read_sql_query("SELECT * FROM db_feedback", conn)
    conn.close()

    total_customers = len(df_sub)
    churned_customers = int(df_sub['cancellation_date'].notnull().sum())
    active_customers = total_customers - churned_customers

    churn_rate = round((churned_customers / total_customers * 100), 1) if total_customers > 0 else 0
    retention_rate = round(100.0 - churn_rate, 1)

    monthly_subs = df_sub[df_sub['contract_type'] == 'Monthly']
    annual_subs = df_sub[df_sub['contract_type'] == 'Annual']

    monthly_churn_rate = round((monthly_subs['cancellation_date'].notnull().sum() / len(monthly_subs) * 100), 1) if len(monthly_subs) > 0 else 0
    annual_churn_rate = round((annual_subs['cancellation_date'].notnull().sum() / len(annual_subs) * 100), 1) if len(annual_subs) > 0 else 0

    total_revenue = float(df_sub['monthly_charges'].sum())
    active_revenue = float(df_sub[df_sub['cancellation_date'].isnull()]['monthly_charges'].sum())
    arpu = round(active_revenue / active_customers, 2) if active_customers > 0 else 0

    revenue_loss = float(df_sub[df_sub['cancellation_date'].notnull()]['monthly_charges'].sum())
    cltv_lost = float(df_sub[df_sub['cancellation_date'].notnull()]['cltv'].sum())

    high_risk_count = int((df_sub['churn_score'] > 70).sum())
    med_risk_count = int(((df_sub['churn_score'] >= 40) & (df_sub['churn_score'] <= 70)).sum())
    low_risk_count = int((df_sub['churn_score'] < 40).sum())

    total_emails = len(df_out)
    replied_emails = len(df_out[df_out['status'].str.contains('Replied', case=False, na=False)])
    reply_rate = round((replied_emails / total_emails * 100), 1) if total_emails > 0 else 0

    return jsonify({
        "total_customers": total_customers,
        "active_customers": active_customers,
        "churned_customers": churned_customers,
        "churn_rate": churn_rate,
        "retention_rate": retention_rate,
        "monthly_churn_rate": monthly_churn_rate,
        "annual_churn_rate": annual_churn_rate,
        "arpu": arpu,
        "total_revenue": total_revenue,
        "revenue_loss": revenue_loss,
        "cltv_lost": cltv_lost,
        "risk_breakdown": {
            "high": high_risk_count,
            "medium": med_risk_count,
            "low": low_risk_count
        },
        "email_analytics": {
            "total_sent": total_emails,
            "replied": replied_emails,
            "reply_rate": reply_rate
        },
        "ml_accuracy": round(predictor.metrics.get('accuracy', 1.0) * 100, 1)
    })

# API 2: Customer Explorer with Live Search, Multi-Filtering & Sorting
@app.route('/api/customers', methods=['GET'])
def get_customers():
    search_query = request.args.get('search', '').lower().strip()
    risk_filter = request.args.get('risk', '').upper().strip()
    contract_filter = request.args.get('contract', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_by = request.args.get('sort', 'highest_risk').strip()

    conn = get_db_connection()
    query = """
    SELECT 
        c.customerid,
        c.name,
        c.email,
        c.phone,
        c.State,
        s.plan_type,
        s.contract_type,
        s.monthly_charges,
        s.cltv,
        s.churn_score,
        s.cancellation_date,
        s.cancellation_reason,
        COALESCE(sup.escalation_count, 0) AS escalations
    FROM db_customer c
    JOIN db_subscription s ON c.customerid = s.customerid
    LEFT JOIN (
        SELECT customerid, SUM(Escalations) AS escalation_count
        FROM db_support GROUP BY customerid
    ) sup ON c.customerid = sup.customerid
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df['is_churned'] = df['cancellation_date'].notnull().astype(int)
    
    # Calculate Risk Score & Level
    def get_risk_info(row):
        score = row['churn_score']
        if score > 70:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"
        return level

    df['risk_level'] = df.apply(get_risk_info, axis=1)

    # Search filtering
    if search_query:
        df = df[df['name'].str.lower().str.contains(search_query) | df['email'].str.lower().str.contains(search_query)]

    if risk_filter in ['HIGH', 'MEDIUM', 'LOW']:
        df = df[df['risk_level'] == risk_filter]

    if contract_filter in ['Monthly', 'Annual']:
        df = df[df['contract_type'] == contract_filter]

    if status_filter == 'Churned':
        df = df[df['is_churned'] == 1]
    elif status_filter == 'Active':
        df = df[df['is_churned'] == 0]

    # Sorting
    if sort_by == 'highest_risk':
        df = df.sort_values(by='churn_score', ascending=False)
    elif sort_by == 'highest_revenue':
        df = df.sort_values(by='monthly_charges', ascending=False)
    elif sort_by == 'recent_churn':
        df = df.sort_values(by='cancellation_date', ascending=False, na_position='last')

    customers_list = df.to_dict(orient='records')
    return jsonify({"count": len(customers_list), "customers": customers_list})

# API 3: Detailed Customer Profile & Activity Timeline
@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer_profile(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.*, s.subscription_start_date, s.renewal_date, s.plan_type, s.contract_type, 
           s.cancellation_date, s.cancellation_reason, s.monthly_charges, s.cltv, s.churn_score
    FROM db_customer c
    JOIN db_subscription s ON c.customerid = s.customerid
    WHERE c.customerid = ?
    """, (customer_id,))
    cust_row = cursor.fetchone()

    if not cust_row:
        conn.close()
        return jsonify({"error": "Customer not found"}), 404

    cust_dict = dict(cust_row)

    # Support Tickets
    cursor.execute("SELECT * FROM db_support WHERE customerid = ?", (customer_id,))
    tickets = [dict(r) for r in cursor.fetchall()]

    # Outreach Log History
    cursor.execute("SELECT * FROM db_outreach_log WHERE customerid = ? ORDER BY log_id DESC", (customer_id,))
    outreach = [dict(r) for r in cursor.fetchall()]

    # Feedback Logs
    cursor.execute("SELECT * FROM db_feedback WHERE customerid = ? ORDER BY feedback_id DESC", (customer_id,))
    feedbacks = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Get ML Churn Prediction & Risk Score Factors
    ml_pred = predictor.predict_customer(customer_id)

    # Build Chronological Customer Activity Timeline
    timeline = []

    if cust_dict.get('subscription_start_date'):
        timeline.append({
            "date": cust_dict['subscription_start_date'],
            "event": "Subscription Started",
            "detail": f"Subscribed to {cust_dict['plan_type']} ({cust_dict['contract_type']}) Tier at ${cust_dict['monthly_charges']}/mo",
            "type": "start"
        })

    for t in tickets:
        timeline.append({
            "date": t.get('complaint_date', '2024-08-15'),
            "event": "Support Complaint Logged",
            "detail": f"Category: {t.get('col_1')} | Escalated: {'Yes (Urgent)' if t.get('Escalations')==1 else 'No'} | CSAT: {t.get('csat_score')}/5",
            "type": "warning" if t.get('Escalations')==1 else "info"
        })

    if cust_dict.get('churn_score', 0) > 70:
        timeline.append({
            "date": "2024-09-01",
            "event": "Risk Score Flagged HIGH",
            "detail": f"Churn Risk Score elevated to {cust_dict['churn_score']}/100 due to support friction & contract tier.",
            "type": "danger"
        })

    for o in outreach:
        timeline.append({
            "date": o.get('contact_date'),
            "event": f"Email Dispatched: {o.get('contact_type')}",
            "detail": f"Subject: {o.get('email_subject')} | Status: {o.get('status')}",
            "type": "outreach"
        })

    for f in feedbacks:
        timeline.append({
            "date": f.get('submitted_at'),
            "event": "Customer Exit Survey Feedback Received",
            "detail": f"Reason: {f.get('reason_category')} | Comment: '{f.get('comment')}'",
            "type": "feedback"
        })

    if cust_dict.get('cancellation_date'):
        timeline.append({
            "date": cust_dict['cancellation_date'],
            "event": "Subscription Cancelled",
            "detail": f"Reason logged: {cust_dict.get('cancellation_reason')}",
            "type": "cancelled"
        })

    timeline.sort(key=lambda x: str(x['date']))

    # Strategic Retention Recommendation Engine
    reason_lower = str(cust_dict.get('cancellation_reason', '')).lower()
    if 'price' in reason_lower:
        rec_action = "Offer 20% discount for 12 months on Annual Standard Tier."
    elif 'competitor' in reason_lower:
        rec_action = "Match competitor pricing + Add 1 Month Free VIP HD Pass."
    elif 'tech' in reason_lower or 'lag' in reason_lower:
        rec_action = "Assign Priority Support SLA + Credit $15 Service Recovery Code."
    elif 'support' in reason_lower or 'service' in reason_lower:
        rec_action = "Direct Call from Customer Success Manager + 30 Days Free Renewal."
    else:
        rec_action = "Trigger Personalized Exit Survey Email with 30% Discount Code."

    return jsonify({
        "customer": cust_dict,
        "ml_risk": ml_pred,
        "support_tickets": tickets,
        "outreach_history": outreach,
        "feedback_history": feedbacks,
        "activity_timeline": timeline,
        "recommended_action": rec_action
    })

# API 4: Email Template List & Live Preview Generator
@app.route('/api/email/templates', methods=['GET'])
def get_templates():
    return jsonify({"templates": EMAIL_TEMPLATES})

@app.route('/api/email/preview', methods=['POST'])
def preview_email():
    data = request.json or {}
    customer_id = data.get('customer_id', 101)
    template_key = data.get('template_key', 'exit_survey')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.name, c.email, c.State, s.plan_type, s.cancellation_reason 
    FROM db_customer c JOIN db_subscription s ON c.customerid = s.customerid WHERE c.customerid = ?
    """, (customer_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Customer not found"}), 404

    name, email, state, plan, reason = row[0], row[1], row[2], row[3], row[4] or "Price Hike"
    subj, body = generate_template_email(template_key, name, plan, state, reason)

    return jsonify({
        "customer_id": customer_id,
        "name": name,
        "email": email,
        "template_key": template_key,
        "subject": subj,
        "body": body
    })

# API 5: Send Single Retention Email
@app.route('/api/email/send', methods=['POST'])
def send_email():
    data = request.json or {}
    customer_id = data.get('customer_id')
    template_key = data.get('template_key', 'exit_survey')
    custom_subject = data.get('custom_subject')
    custom_body = data.get('custom_body')

    if not customer_id:
        return jsonify({"error": "Missing customer_id"}), 400

    result = send_customer_email(customer_id, template_key, custom_subject, custom_body)
    return jsonify(result)

# API 6: Launch Retention Campaign
@app.route('/api/campaign/create', methods=['POST'])
def create_campaign():
    data = request.json or {}
    campaign_name = data.get('campaign_name', 'Price Sensitivity Campaign')
    target_audience = data.get('target_audience', 'High Risk Basic Monthly')
    template_key = data.get('template_key', 'price_sensitivity')

    conn = get_db_connection()
    df_churned = pd.read_sql_query("""
    SELECT c.customerid, c.name, c.email 
    FROM db_customer c JOIN db_subscription s ON c.customerid = s.customerid
    WHERE s.cancellation_date IS NOT NULL
    """, conn)
    conn.close()

    sent_count = 0
    for _, row in df_churned.iterrows():
        send_customer_email(row['customerid'], template_key)
        sent_count += 1

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO db_campaign (campaign_name, target_audience, total_targeted, sent_count, response_count, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (campaign_name, target_audience, len(df_churned), sent_count, 0, created_at))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "campaign_name": campaign_name,
        "total_targeted": len(df_churned),
        "sent_count": sent_count,
        "created_at": created_at
    })

# API 7: Submit Customer Survey Feedback (Public Endpoint)
@app.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    data = request.json or {}
    customer_id = data.get('customer_id')
    reason_category = data.get('reason_category', 'Price Sensitivity')
    comment = data.get('comment', '')

    if not customer_id:
        return jsonify({"error": "Missing customer_id"}), 400

    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if "price" in reason_category.lower() or "expensive" in comment.lower():
        rec_action = "Offer 20% Annual Discount"
    elif "competitor" in reason_category.lower():
        rec_action = "Match Competitor Annual Bundle Deal"
    elif "support" in reason_category.lower():
        rec_action = "Priority SLA + 30 Days Credit"
    else:
        rec_action = "General Re-activation Offer"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO db_feedback (customerid, reason_category, comment, submitted_at, recommended_action)
    VALUES (?, ?, ?, ?, ?)
    """, (customer_id, reason_category, comment, submitted_at, rec_action))

    # Update subscription cancellation reason & outreach status
    cursor.execute("""
    UPDATE db_subscription SET cancellation_reason = ? WHERE customerid = ?
    """, (f"{reason_category}: {comment}", customer_id))

    cursor.execute("""
    UPDATE db_outreach_log SET status = 'Replied - Feedback Logged', customer_feedback = ?
    WHERE customerid = ? AND status = 'Sent'
    """, (comment, customer_id))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "customer_id": customer_id,
        "category": reason_category,
        "recommended_action": rec_action,
        "submitted_at": submitted_at
    })

# API 8: Get Live Sent Email Outbox Logs
@app.route('/api/email/outbox', methods=['GET'])
def get_outbox():
    conn = get_db_connection()
    query = """
    SELECT o.*, c.name 
    FROM db_outreach_log o
    JOIN db_customer c ON o.customerid = c.customerid
    ORDER BY o.log_id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return jsonify({"count": len(df), "logs": df.to_dict(orient='records')})

# API 9: Export Reports to CSV or Excel
@app.route('/api/reports/export', methods=['GET'])
def export_reports():
    fmt = request.args.get('format', 'csv').lower()
    conn = get_db_connection()
    query = """
    SELECT 
        c.customerid AS "Customer ID",
        c.name AS "Customer Name",
        c.email AS "Email Address",
        c.phone AS "Phone Number",
        c.State AS "State",
        s.plan_type AS "Plan Tier",
        s.contract_type AS "Contract Structure",
        s.monthly_charges AS "Monthly Charges ($)",
        s.cltv AS "Customer Lifetime Value ($)",
        s.churn_score AS "Churn Risk Score (0-100)",
        s.cancellation_date AS "Cancellation Date",
        s.cancellation_reason AS "Cancellation Reason"
    FROM db_customer c
    JOIN db_subscription s ON c.customerid = s.customerid
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    os.makedirs("exports", exist_ok=True)
    filename = f"ChurnGuard_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if fmt == 'excel':
        filepath = os.path.join("exports", f"{filename}.xlsx")
        df.to_excel(filepath, index=False, engine='openpyxl')
        return send_file(filepath, as_attachment=True, download_name=f"{filename}.xlsx")
    else:
        filepath = os.path.join("exports", f"{filename}.csv")
        df.to_csv(filepath, index=False)
        return send_file(filepath, as_attachment=True, download_name=f"{filename}.csv")

if __name__ == '__main__':
    print("=" * 70)
    print("      CHURNGUARD WEB APPLICATION SERVER RUNNING")
    print("      Server URL: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host='127.0.0.1', port=5000, debug=True)
