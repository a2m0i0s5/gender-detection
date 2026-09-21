import sqlite3
import pandas as pd
import json

DB_PATH = "customer_churn.db"

class AISmartDataAnalyst:
    """AI Smart Data Analyst & Personalized Offer/Ad Recommendation Engine."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def analyze_customer(self, customer_id):
        """Automatically reads customer data, detects behavioral patterns, and generates personalized offers & targeted ads."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
        SELECT c.*, s.plan_type, s.contract_type, s.monthly_charges, s.cltv, s.churn_score, s.cancellation_reason
        FROM db_customer c
        JOIN db_subscription s ON c.customerid = s.customerid
        WHERE c.customerid = ?
        """, (customer_id,))
        cust = cursor.fetchone()

        if not cust:
            conn.close()
            return {"error": "Customer not found"}

        cust_dict = dict(cust)

        # Support complaints analysis
        cursor.execute("SELECT * FROM db_support WHERE customerid = ?", (customer_id,))
        tickets = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # AI Behavior Analysis
        interests = str(cust_dict.get('interests', '')).lower()
        reason = str(cust_dict.get('cancellation_reason', '')).lower()
        score = cust_dict.get('churn_score', 0)
        escalations = sum([1 for t in tickets if t.get('Escalations') == 1])

        # Rule & Heuristic AI Pattern Matching
        if 'price' in reason or 'expensive' in reason or (score > 70 and cust_dict['plan_type'] == 'Basic'):
            cohort = "Price Sensitive Basic Subscribers"
            analyst_insight = f"Customer {cust_dict['name']} shows high price sensitivity following recent tariff updates in {cust_dict['State']}. Monthly cost of ${cust_dict['monthly_charges']} exceeds perceived basic tier value."
            offer_title = "20% Discount + Price Lock Protection"
            offer_code = "PRICELOCK20"
            ad_headline = "🎬 Never Pay Extra for Your Favorite Shows!"
            ad_subtext = "Upgrade to Annual Standard today for only $13.50/mo. Lock in your rate for 12 full months."
            ad_cta = "Claim 20% Price Lock Offer"
            recommended_channel = "Email & In-App Banner"

        elif 'tech' in reason or 'lag' in reason or any('lag' in str(t.get('col_1','')).lower() for t in tickets):
            cohort = "Technical Performance Dissatisfied"
            analyst_insight = f"Customer {cust_dict['name']} logged streaming lag complaints. Video buffer latency is impacting satisfaction on their live broadcast streams."
            offer_title = "StreamTurbo Ultra HD Pass Free for 30 Days"
            offer_code = "TURBOHD30"
            ad_headline = "⚡ Zero Buffering. 100% Ultra HD Quality."
            ad_subtext = "We upgraded our servers in your region! Experience lightning-fast 4K streaming with zero lag."
            ad_cta = "Activate Free 30-Day StreamTurbo"
            recommended_channel = "Direct Push Notification & Email"

        elif 'competitor' in reason or any('competitor' in str(t.get('col_1','')).lower() for t in tickets):
            cohort = "Competitor Switch Vulnerability"
            analyst_insight = f"Customer {cust_dict['name']} is evaluating rival OTT platforms offering annual bundle deals."
            offer_title = "Competitor Match: 1 Month Free + Unlimited Downloads"
            offer_code = "MATCHPROMO"
            ad_headline = "🏆 Why Settle for Less? Get More on StreamFlix!"
            ad_subtext = "We will match any competitor offer + give you 1 Month Free VIP HD Pass."
            ad_cta = "Claim Competitor Match Deal"
            recommended_channel = "VIP Email Outreach"

        elif 'sports' in interests or 'action' in interests:
            cohort = "Sports & Action Enthusiasts"
            analyst_insight = f"Customer {cust_dict['name']} frequently streams live sports and action movies. High potential for Premium Live Sports Add-on."
            offer_title = "Live Sports HD Pass 50% Off"
            offer_code = "SPORT50"
            ad_headline = "⚽ Never Miss a Goal in Ultra HD!"
            ad_subtext = "Get exclusive access to all live matches with 50% off the Live Sports Pass."
            ad_cta = "Unlock 50% Off Sports Pass"
            recommended_channel = "In-App Ad Carousel"

        else:
            cohort = "General Subscriber Cohort"
            analyst_insight = f"Customer {cust_dict['name']} has an active profile. Engagement is moderate; recommending loyalty reward upgrade."
            offer_title = "Loyalty Upgrade: Free Upgrade to Standard Tier for 60 Days"
            offer_code = "LOYALTY60"
            ad_headline = "🎁 A Special Loyalty Gift Just for You!"
            ad_subtext = "Enjoy 2 HD Screens and Offline Downloads on us for the next 60 days."
            ad_cta = "Claim Free Tier Upgrade"
            recommended_channel = "In-App Popup"

        return {
            "customer_id": customer_id,
            "name": cust_dict['name'],
            "email": cust_dict['email'],
            "cohort": cohort,
            "analyst_insight": analyst_insight,
            "personalized_offer": {
                "title": offer_title,
                "code": offer_code,
                "channel": recommended_channel
            },
            "targeted_ad": {
                "headline": ad_headline,
                "subtext": ad_subtext,
                "cta_button": ad_cta,
                "banner_theme": "dark-glassmorphism"
            }
        }

    def generate_all_cohort_ads(self):
        """Generates targeted ad campaign previews for all customer cohorts."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT customerid FROM db_customer")
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            res = self.analyze_customer(r['customerid'])
            results.append(res)

        return results

ai_analyst = AISmartDataAnalyst()

if __name__ == "__main__":
    print("=== AI Smart Data Analyst Test ===")
    res = ai_analyst.analyze_customer(101)
    print(json.dumps(res, indent=2))
