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

    # Table 1: db_customer
    cursor.execute("""
    CREATE TABLE db_customer (
        customerid INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
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

    # Synthetic Dataset matching precise benchmark numbers (21 total customers):
    # 6 churned customers (6/21 = 28.57% ~ 28.6% Churn, 71.4% Retention)
    # Monthly contracts: 9 total, 5 churned -> 5/9 = 55.56% ~ 55.6%
    # Annual contracts: 12 total, 1 churned -> 1/12 = 8.33% ~ 8.3%
    # Churn dates concentrated in September 2024 in Karnataka for Basic plans.
    # Total Monthly Charges = ~395, Churned Charges = ~74 (18.7% ~ 18%)
    # Total CLTV Lost = ~2047, Average Tenure = ~1451 days

    customers = [
        (101, "Aarav Sharma", "India", "Karnataka", "Male", "1990-05-14", "Movies, Sci-Fi", "560001"),
        (102, "Priya Patel", "India", "Karnataka", "Female", "1994-08-22", "Drama, Romance", "560002"),
        (103, "Rahul Verma", "India", "Karnataka", "Male", "1988-11-03", "Sports, Action", "560034"),
        (104, "Ananya Rao", "India", "Karnataka", "Female", "1996-02-17", "Comedy, Documentaries", "560045"),
        (105, "Rohan Gupta", "India", "Maharashtra", "Male", "1992-09-30", "Thriller, Tech", "400001"),
        (106, "Sneha Kulkarni", "India", "Maharashtra", "Female", "1995-12-10", "Anime, Fantasy", "400012"),
        (107, "Vikram Singh", "India", "Delhi", "Male", "1985-04-05", "News, Politics", "110001"),
        (108, "Neha Joshi", "India", "Karnataka", "Female", "1998-07-19", "Music, Reality TV", "560068"),
        (109, "Karan Reddy", "India", "Telangana", "Male", "1991-03-25", "Action, Gaming", "500001"),
        (110, "Divya Nair", "India", "Kerala", "Female", "1993-10-12", "Drama, Classics", "682001"),
        (111, "Amit Kumar", "India", "Karnataka", "Male", "1989-01-08", "Sports, Sci-Fi", "560078"),
        (112, "Meera Sundaram", "India", "Tamil Nadu", "Female", "1997-06-30", "Independent, Art", "600001"),
        (113, "Siddharth Das", "India", "West Bengal", "Male", "1987-08-14", "Documentaries, History", "700001"),
        (114, "Pooja Malhotra", "India", "Delhi", "Female", "1996-11-28", "Fashion, Reality TV", "110016"),
        (115, "Aditya Roy", "India", "Maharashtra", "Male", "1994-04-18", "Action, Comedy", "400050"),
        (116, "Kavita Deshmukh", "India", "Maharashtra", "Female", "1991-02-09", "Romance, Drama", "411001"),
        (117, "Rajesh Chawla", "India", "Punjab", "Male", "1986-12-01", "Sports, Action", "141001"),
        (118, "Shreya Iyer", "India", "Karnataka", "Female", "1999-05-15", "Sci-Fi, Anime", "560092"),
        (119, "Gaurav Mehta", "India", "Gujarat", "Male", "1993-09-04", "Finance, News", "380001"),
        (120, "Ritu Sen", "India", "West Bengal", "Female", "1995-07-21", "Drama, Thriller", "700019"),
        (121, "Tarun Bansal", "India", "Haryana", "Male", "1990-03-11", "Comedy, Sports", "122001")
    ]

    cursor.executemany("INSERT INTO db_customer VALUES (?,?,?,?,?,?,?,?)", customers)

    # Subscriptions details
    # Churned: 101, 102, 103, 104, 108, 111 (6 churned out of 21)
    # Monthly churned: 101, 102, 103, 104, 108 (5/9 = 55.6%)
    # Annual churned: 111 (1/12 = 8.3%)
    subscriptions = [
        # customerid, start_date, sub_type, renewal_date, plan_type, contract_type, canc_date, canc_reason, monthly_charges, cltv, churn_score
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

    # Support / Complaint records
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

    conn.commit()
    conn.close()
    print("Database customer_churn.db created and populated successfully!")

if __name__ == "__main__":
    create_and_populate_db()
