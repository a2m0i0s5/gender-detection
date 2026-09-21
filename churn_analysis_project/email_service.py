import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

DB_PATH = "customer_churn.db"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "support@streamflix-ott.com")

EMAIL_TEMPLATES = {
    "exit_survey": {
        "title": "Exit Survey & Feedback Request",
        "subject": "StreamFlix Care: We noticed you left - Help us improve, {name}!",
        "body": """Dear {name},

We noticed that your StreamFlix {plan} tier subscription was recently cancelled. 

We are deeply committed to providing the best streaming experience. Could you take 30 seconds to let us know why you left?

Logged Reason: [{reason}]

To show our appreciation, if you share your feedback or decide to rejoin us today, we will credit 30% off your next 3 months of streaming!

Warm regards,
Customer Retention Team
StreamFlix OTT Platform
"""
    },
    "retention_offer": {
        "title": "30% Discount Retention Offer",
        "subject": "Special Re-activation Deal for {name} - 30% Off StreamFlix!",
        "body": """Dear {name},

We miss having you on StreamFlix! 

Based on your streaming history, we have unlocked an exclusive 30% discount on your next 3 months if you reactivate your {plan} plan today.

Use Promo Code: STAY30 at checkout.

Warm regards,
Growth & Retention Team
StreamFlix OTT Platform
"""
    },
    "price_sensitivity": {
        "title": "Price Concern & Annual Tier Discount",
        "subject": "Exclusive Tariff Price Protection for {name}",
        "body": """Dear {name},

We understand that subscription costs matter. Following our recent price adjustment in {state}, we are offering you price protection:

Lock in your StreamFlix subscription at your old rate by migrating to our Annual Standard tier at 20% off!

Claim your price lock now with one click.

Warm regards,
Pricing & Retention Specialist
StreamFlix OTT Platform
"""
    },
    "competitor_match": {
        "title": "Competitor Deal Match Campaign",
        "subject": "We will match rival OTT deals for you, {name}!",
        "body": """Dear {name},

Before you switch to a competitor, let us match their deal! We are adding 1 Month Free access + Unlimited HD Downloads to your StreamFlix account if you stay with us.

Reply to this email directly to claim your competitor price match.

Warm regards,
VIP Customer Care
StreamFlix OTT Platform
"""
    },
    "service_recovery": {
        "title": "Priority Support & Service Recovery",
        "subject": "Apology from StreamFlix Support Team + Free Trial Credit",
        "body": """Dear {name},

We sincerely apologize for the recent technical playback or support delay you experienced.

We have assigned a dedicated VIP support manager to your profile and credited 1 Month of Free Access to your account.

We hope to welcome you back!

Warm regards,
Head of Customer Support
StreamFlix OTT Platform
"""
    }
}

def generate_template_email(template_key, name, plan="Basic", state="Karnataka", reason="Price Sensitivity"):
    """Generate email subject and body from template key."""
    t = EMAIL_TEMPLATES.get(template_key, EMAIL_TEMPLATES["exit_survey"])
    subj = t["subject"].format(name=name, plan=plan, state=state, reason=reason)
    body = t["body"].format(name=name, plan=plan, state=state, reason=reason)
    return subj, body

def deliver_email_via_smtp(to_email, subject, body):
    """Attempt real SMTP delivery via smtplib if credentials exist."""
    if not SMTP_USERNAME or "your_app" in SMTP_PASSWORD or not SMTP_PASSWORD:
        # Fallback to simulated delivery
        msg_id = f"SIM-MSG-{int(datetime.now().timestamp())}"
        return True, msg_id, "Simulated Dispatch (SMTP Credentials Not Configured in .env)"

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
        server.quit()

        msg_id = f"SMTP-MSG-{int(datetime.now().timestamp())}"
        return True, msg_id, "Delivered via Real SMTP"
    except Exception as e:
        return False, None, str(e)

def send_customer_email(customer_id, template_key="exit_survey", custom_subject=None, custom_body=None):
    """Send retention email to customer and log status into db_outreach_log."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.name, c.email, c.State, s.plan_type, s.cancellation_reason 
    FROM db_customer c
    JOIN db_subscription s ON c.customerid = s.customerid
    WHERE c.customerid = ?
    """, (customer_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"status": "error", "message": f"Customer ID {customer_id} not found."}

    name, email, state, plan, reason = row
    reason = reason or "Price Increase"

    if custom_subject and custom_body:
        subj, body = custom_subject, custom_body
    else:
        subj, body = generate_template_email(template_key, name, plan, state, reason)

    # Deliver via SMTP or Simulated Engine
    success, msg_id, err_note = deliver_email_via_smtp(email, subj, body)
    status = "Sent" if success else "Failed"
    contact_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO db_outreach_log
    (customerid, contact_date, contact_type, email_address, email_subject, email_body, customer_feedback, categorized_reason, status, message_id, error_message)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, contact_date, f"Email ({template_key})", email, subj, body, "Pending Response", reason, status, msg_id, err_note))

    conn.commit()
    conn.close()

    return {
        "status": "success" if success else "error",
        "customerid": customer_id,
        "name": name,
        "email": email,
        "subject": subj,
        "body": body,
        "sent_at": contact_date,
        "delivery_status": status,
        "message_id": msg_id,
        "note": err_note
    }

if __name__ == "__main__":
    res = send_customer_email(101, "price_sensitivity")
    print("Email Service Test Result:", res)
