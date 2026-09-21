import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_and_populate_db():
    db_name = "customer_churn.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Drop existing tables if re-running
    cursor.execute("DROP TABLE IF EXISTS db_customer")
    cursor.execute("DROP TABLE IF EXISTS db_subscription")
    cursor.execute("DROP TABLE IF EXISTS db_support")
    cursor.execute("DROP TABLE IF EXISTS db_outreach_log")

    # Table 1: db_customer (Enhanced with email and phone)
    cursor.execute("""
    CREATE TABLE db_customer (
        customerid INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        country TEXT NOT NULL,
        State TEXT NOT NULL,
        gender TEXT NOT NULL,
        dob TEXT NOT NULL,
        interests TEXT,
        pincode TEXT
    )
    """)

    # Table 2: db_subscription
    cursor.execute("""
    CREATE TABLE db_subscription (
        customerid INTEGER PRIMARY KEY,
        subscription_start_date TEXT NOT NULL,
        subscription_type TEXT NOT NULL,
        renewal_date TEXT NOT NULL,
        plan_type TEXT NOT NULL,
        contract_type TEXT NOT NULL,
        cancellation_date TEXT,
        cancellation_reason TEXT,
        monthly_charges REAL NOT NULL,
        cltv REAL NOT NULL,
        churn_score INTEGER NOT NULL,
        FOREIGN KEY (customerid) REFERENCES db_customer(customerid)
    )
    """)

    # Table 3: db_support
    cursor.execute("""
    CREATE TABLE db_support (
        support_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customerid INTEGER NOT NULL,
        complaint_date TEXT,
        Escalations INTEGER NOT NULL,
        csat_score INTEGER,
        col_1 TEXT,
        comment TEXT,
        FOREIGN KEY (customerid) REFERENCES db_customer(customerid)
    )
    """)

    # Table 4: db_outreach_log (NEW: Direct Email & Customer Response Tracking)
    cursor.execute("""
    CREATE TABLE db_outreach_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customerid INTEGER NOT NULL,
        contact_date TEXT NOT NULL,
        contact_type TEXT NOT NULL,
        email_address TEXT NOT NULL,
        email_subject TEXT NOT NULL,
        email_body TEXT NOT NULL,
        customer_feedback TEXT,
        categorized_reason TEXT,
        status TEXT NOT NULL,
        FOREIGN KEY (customerid) REFERENCES db_customer(customerid)
    )
    """)

    # Customers with explicit email and contact numbers
    customers = [
        (101, "Aarav Sharma", "aarav.sharma@example.com", "+91-9876543210", "India", "Karnataka", "Male", "1990-05-14", "Movies, Sci-Fi", "560001"),
        (102, "Priya Patel", "priya.patel@example.com", "+91-9876543211", "India", "Karnataka", "Female", "1994-08-22", "Drama, Romance", "560002"),
        (103, "Rahul Verma", "rahul.verma@example.com", "+91-9876543212", "India", "Karnataka", "Male", "1988-11-03", "Sports, Action", "560034"),
        (104, "Ananya Rao", "ananya.rao@example.com", "+91-9876543213", "India", "Karnataka", "Female", "1996-02-17", "Comedy, Documentaries", "560045"),
        (105, "Rohan Gupta", "rohan.gupta@example.com", "+91-9876543214", "India", "Maharashtra", "Male", "1992-09-30", "Thriller, Tech", "400001"),
        (106, "Sneha Kulkarni", "sneha.kulkarni@example.com", "+91-9876543215", "India", "Maharashtra", "Female", "1995-12-10", "Anime, Fantasy", "400012"),
        (107, "Vikram Singh", "vikram.singh@example.com", "+91-9876543216", "India", "Delhi", "Male", "1985-04-05", "News, Politics", "110001"),
        (108, "Neha Joshi", "neha.joshi@example.com", "+91-9876543217", "India", "Karnataka", "Female", "1998-07-19", "Music, Reality TV", "560068"),
        (109, "Karan Reddy", "karan.reddy@example.com", "+91-9876543218", "India", "Telangana", "Male", "1991-03-25", "Action, Gaming", "500001"),
        (110, "Divya Nair", "divya.nair@example.com", "+91-9876543219", "India", "Kerala", "Female", "1993-10-12", "Drama, Classics", "682001"),
        (111, "Amit Kumar", "amit.kumar@example.com", "+91-9876543220", "India", "Karnataka", "Male", "1989-01-08", "Sports, Sci-Fi", "560078"),
        (112, "Meera Sundaram", "meera.sundaram@example.com", "+91-9876543221", "India", "Tamil Nadu", "Female", "1997-06-30", "Independent, Art", "600001"),
        (113, "Siddharth Das", "siddharth.das@example.com", "+91-9876543222", "India", "West Bengal", "Male", "1987-08-14", "Documentaries, History", "700001"),
        (114, "Pooja Malhotra", "pooja.malhotra@example.com", "+91-9876543223", "India", "Delhi", "Female", "1996-11-28", "Fashion, Reality TV", "110016"),
        (115, "Aditya Roy", "aditya.roy@example.com", "+91-9876543224", "India", "Maharashtra", "Male", "1994-04-18", "Action, Comedy", "400050"),
        (116, "Kavita Deshmukh", "kavita.deshmukh@example.com", "+91-9876543225", "India", "Maharashtra", "Female", "1991-02-09", "Romance, Drama", "411001"),
        (117, "Rajesh Chawla", "rajesh.chawla@example.com", "+91-9876543226", "India", "Punjab", "Male", "1986-12-01", "Sports, Action", "141001"),
        (118, "Shreya Iyer", "shreya.iyer@example.com", "+91-9876543227", "India", "Karnataka", "Female", "1999-05-15", "Sci-Fi, Anime", "560092"),
        (119, "Gaurav Mehta", "gaurav.mehta@example.com", "+91-9876543228", "India", "Gujarat", "Male", "1993-09-04", "Finance, News", "380001"),
        (120, "Ritu Sen", "ritu.sen@example.com", "+91-9876543229", "India", "West Bengal", "Female", "1995-07-21", "Drama, Thriller", "700019"),
        (121, "Tarun Bansal", "tarun.bansal@example.com", "+91-9876543230", "India", "Haryana", "Male", "1990-03-11", "Comedy, Sports", "122001")
    ]

    cursor.executemany("INSERT INTO db_customer VALUES (?,?,?,?,?,?,?,?,?,?)", customers)

    # Subscriptions details
    subscriptions = [
        (101, "2020-01-15", "Streaming", "2024-09-15", "Basic", "Monthly", "2024-09-15", "Price Hike in Sep", 14.99, 320.00, 85),
        (102, "2020-03-10", "Streaming", "2024-09-18", "Basic", "Monthly", "2024-09-18", "Moved to Competitor", 12.50, 290.00, 90),
        (103, "2019-11-20", "Streaming", "2024-09-05", "Basic", "Monthly", "2024-09-05", "Tech Issues / Streaming Lag", 11.99, 350.00, 78),
        (104, "2021-02-14", "Streaming", "2024-09-22", "Basic", "Monthly", "2024-09-22", "Unsatisfied with Content", 13.00, 240.00, 82),
        (105, "2019-06-01", "Streaming", "2025-06-01", "Premium", "Annual", None, None, 22.00, 850.00, 15),
        (106, "2020-08-19", "Streaming", "2025-08-19", "Standard", "Annual", None, None, 18.00, 620.00, 25),
        (107, "2018-05-12", "Streaming", "2025-05-12", "Premium", "Annual", None, None, 24.50, 940.00, 10),
        (108, "2021-07-04", "Streaming", "2024-09-10", "Basic", "Monthly", "2024-09-10", "Competitor Offer", 11.50, 210.00, 88),
        (109, "2020-10-30", "Streaming", "2025-10-30", "Standard", "Annual", None, None, 17.50, 580.00, 30),
        (110, "2019-04-15", "Streaming", "2025-04-15", "Premium", "Annual", None, None, 25.00, 980.00, 12),
        (111, "2020-02-28", "Streaming", "2024-09-29", "Basic", "Annual", "2024-09-29", "Service Dissatisfaction", 9.96, 637.00, 75),
        (112, "2021-09-14", "Streaming", "2025-09-14", "Standard", "Annual", None, None, 16.50, 490.00, 20),
        (113, "2018-12-01", "Streaming", "2025-12-01", "Premium", "Annual", None, None, 23.00, 890.00, 18),
        (114, "2022-01-10", "Streaming", "2025-02-10", "Standard", "Monthly", None, None, 17.00, 360.00, 42),
        (115, "2020-11-11", "Streaming", "2025-11-11", "Premium", "Annual", None, None, 22.50, 750.00, 22),
        (116, "2019-08-25", "Streaming", "2025-08-25", "Standard", "Annual", None, None, 18.50, 640.00, 28),
        (117, "2018-03-03", "Streaming", "2025-03-03", "Premium", "Annual", None, None, 24.00, 910.00, 15),
        (118, "2022-04-18", "Streaming", "2025-03-18", "Basic", "Monthly", None, None, 12.00, 220.00, 48),
        (119, "2020-07-22", "Streaming", "2025-07-22", "Standard", "Annual", None, None, 19.00, 590.00, 32),
        (120, "2021-12-05", "Streaming", "2025-03-05", "Basic", "Monthly", None, None, 13.50, 280.00, 52),
        (121, "2019-10-10", "Streaming", "2025-03-10", "Standard", "Monthly", None, None, 16.00, 410.00, 38)
    ]

    cursor.executemany("INSERT INTO db_subscription VALUES (?,?,?,?,?,?,?,?,?,?,?)", subscriptions)

    # Support records
    supports = [
        (101, "2024-08-30", 1, 1, "Price Hike", "Complained about sudden tariff increase in Karnataka"),
        (101, "2024-09-12", 1, 1, "Billing Error", "Double charged for monthly basic renewal"),
        (102, "2024-09-02", 1, 2, "Competitor Switch", "Requested price match with rival OTT app"),
        (103, "2024-08-25", 1, 1, "Streaming Lag", "App keeps crashing during live broadcast"),
        (104, "2024-09-15", 1, 2, "Content Removal", "Favorite series removed without notification"),
        (108, "2024-09-05", 1, 1, "Account Issue", "Unable to log in across multiple devices"),
        (111, "2024-09-20", 1, 2, "Customer Care", "Agent unresolved ticket after 48 hours"),
        (114, "2024-07-10", 0, 4, "Feature Request", "Asked for offline download feature"),
        (118, "2024-08-14", 0, 3, "General Query", "Inquired about upgrading to Standard tier"),
        (120, "2024-06-20", 0, 3, "Playback", "Subtitles out of sync on smart TV"),
        (105, "2024-01-15", 0, 5, "Feedback", "Great streaming quality and premium UI")
    ]

    cursor.executemany("""
    INSERT INTO db_support (customerid, complaint_date, Escalations, csat_score, col_1, comment)
    VALUES (?,?,?,?,?,?)
    """, supports)

    # Pre-populate initial outreach log examples
    outreach_records = [
        (101, "2024-09-16", "Exit Survey & 20% Retention Offer", "aarav.sharma@example.com", 
         "We miss you at StreamFlix - Help us improve!", 
         "Hi Aarav, we noticed your subscription cancellation. Was it due to the recent price adjustment?", 
         "Subscription got too expensive after recent price revision in Karnataka.", "Price Sensitivity", "Replied - Feedback Recorded"),
        (102, "2024-09-19", "Exit Survey Email", "priya.patel@example.com", 
         "StreamFlix Exit Survey & Special Discount Offer", 
         "Hi Priya, could you tell us why you decided to leave? We would love to offer you 3 months at 50% off.", 
         "Switched to competitor due to annual combo deal.", "Competitor Switch", "Replied - Feedback Recorded"),
        (103, "2024-09-06", "Technical Support Check-in Email", "rahul.verma@example.com", 
         "We apologize for the playback lag issue", 
         "Hi Rahul, our engineering team resolved the streaming buffer issue on your device.", 
         "Video buffering during live matches forced me to cancel.", "Technical Glitch", "Replied - Feedback Recorded")
    ]

    cursor.executemany("""
    INSERT INTO db_outreach_log (customerid, contact_date, contact_type, email_address, email_subject, email_body, customer_feedback, categorized_reason, status)
    VALUES (?,?,?,?,?,?,?,?,?)
    """, outreach_records)

    conn.commit()
    conn.close()
    print("Database customer_churn.db created with enhanced Customer Contact & Email Outreach schema!")

if __name__ == "__main__":
    create_and_populate_db()
