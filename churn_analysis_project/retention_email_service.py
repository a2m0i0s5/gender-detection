import sqlite3
import pandas as pd
import json
from datetime import datetime

DB_PATH = "customer_churn.db"

def get_customer_contact_info(customer_id=None):
    """Retrieve customer email, contact, and churn status from database."""
    conn = sqlite3.connect(DB_PATH)
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
        s.cancellation_reason
    FROM db_customer c
    JOIN db_subscription s ON c.customerid = s.customerid
    """
    if customer_id:
        query += f" WHERE c.customerid = {customer_id}"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def generate_personalized_email(customer):
    """Generate personalized retention / exit survey email body and subject."""
    name = customer['name']
    plan = customer['plan_type']
    reason = customer['cancellation_reason'] or 'Recent Cancellation'
    
    subject = f"StreamFlix Care: We noticed you left - Help us improve, {name}!"
    
    body = f"""Dear {name},

We noticed that your StreamFlix {plan} tier subscription was recently cancelled. 

We are deeply committed to providing the best streaming experience. Could you take 30 seconds to reply and let us know what went wrong?

Reason logged: [{reason}]

To show our appreciation, if you share your feedback or decide to rejoin us today, we would love to offer you a 30% discount on your next 3 months of streaming!

Warm regards,
Customer Retention & Support Team
StreamFlix OTT Platform
Email Contact: support@streamflix-ott.com
"""
    return subject, body

def send_retention_email(customer_id, custom_subject=None, custom_body=None):
    """Simulate emailing the customer and log the transaction into db_outreach_log."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Fetch customer details
    cursor.execute("""
    SELECT c.name, c.email, s.cancellation_reason 
    FROM db_customer c
    JOIN db_subscription s ON c.customerid = s.customerid
    WHERE c.customerid = ?
    """, (customer_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return {"status": "error", "message": f"Customer ID {customer_id} not found."}
    
    name, email, reason = row
    
    if not custom_subject or not custom_body:
        subj, body = generate_personalized_email({'name': name, 'plan_type': 'Streaming', 'cancellation_reason': reason})
    else:
        subj, body = custom_subject, custom_body
        
    contact_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contact_type = "Automated Exit Survey Email"
    status = "Email Sent Successfully"
    
    cursor.execute("""
    INSERT INTO db_outreach_log 
    (customerid, contact_date, contact_type, email_address, email_subject, email_body, customer_feedback, categorized_reason, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, contact_date, contact_type, email, subj, body, "Awaiting Customer Reply", reason, status))
    
    conn.commit()
    conn.close()
    
    print(f"\n[+] Retention Email Dispatched to {name} ({email})")
    print(f"    Subject: {subj}")
    print(f"    Status : Logged into db_outreach_log")
    
    return {
        "status": "success",
        "customerid": customer_id,
        "name": name,
        "email": email,
        "subject": subj,
        "body": body,
        "sent_at": contact_date
    }

def record_customer_response(customer_id, feedback_text, categorized_reason):
    """Record customer response email feedback and update SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    contact_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update outreach log
    cursor.execute("""
    UPDATE db_outreach_log
    SET customer_feedback = ?, categorized_reason = ?, status = 'Replied - Feedback Recorded'
    WHERE customerid = ? AND status LIKE '%Sent%'
    """, (feedback_text, categorized_reason, customer_id))
    
    # Update cancellation reason in subscription table
    cursor.execute("""
    UPDATE db_subscription
    SET cancellation_reason = ?
    WHERE customerid = ?
    """, (f"{categorized_reason}: {feedback_text}", customer_id))
    
    conn.commit()
    conn.close()
    
    print(f"\n[+] Customer Response Recorded for Customer #{customer_id}")
    print(f"    Categorized Reason: {categorized_reason}")
    print(f"    Feedback Snippet   : {feedback_text}")
    
    return {"status": "success", "customerid": customer_id, "updated_reason": categorized_reason}

def batch_email_churned_subscribers():
    """Send retention outreach emails to all churned subscribers."""
    conn = sqlite3.connect(DB_PATH)
    df_churned = pd.read_sql_query("""
    SELECT c.customerid, c.name, c.email 
    FROM db_customer c
    JOIN db_subscription s ON c.customerid = s.customerid
    WHERE s.cancellation_date IS NOT NULL
    """, conn)
    conn.close()
    
    print(f"\n[+] Initiating Batch Retention Email Campaign for {len(df_churned)} Churned Subscribers...")
    results = []
    for _, row in df_churned.iterrows():
        res = send_retention_email(row['customerid'])
        results.append(res)
    
    print(f"[+] Batch Email Campaign Completed successfully! ({len(results)} emails sent)")
    return results

if __name__ == "__main__":
    print("=== StreamFlix Direct Customer Email & Retention Service ===")
    df_contacts = get_customer_contact_info()
    print(df_contacts[['customerid', 'name', 'email', 'cancellation_reason']].head(10))
    batch_email_churned_subscribers()
