import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import os

DB_PATH = "customer_churn.db"

def prepare_feature_dataset():
    """Extract relational dataset and build feature matrix for ML training."""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        s.customerid,
        s.monthly_charges,
        s.cltv,
        s.contract_type,
        s.plan_type,
        s.cancellation_date,
        s.subscription_start_date,
        s.churn_score,
        c.State,
        COALESCE(sup.escalations, 0) AS escalations,
        COALESCE(sup.complaint_count, 0) AS complaint_count,
        COALESCE(sup.avg_csat, 3.5) AS avg_csat
    FROM db_subscription s
    JOIN db_customer c ON s.customerid = c.customerid
    LEFT JOIN (
        SELECT 
            customerid, 
            SUM(Escalations) AS escalations,
            COUNT(*) AS complaint_count,
            AVG(csat_score) AS avg_csat
        FROM db_support
        GROUP BY customerid
    ) sup ON s.customerid = sup.customerid
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df['subscription_start_date'] = pd.to_datetime(df['subscription_start_date'])
    df['cancellation_date'] = pd.to_datetime(df['cancellation_date'])
    analysis_date = pd.to_datetime('2024-10-01')
    
    end_dates = df['cancellation_date'].fillna(analysis_date)
    df['tenure_days'] = (end_dates - df['subscription_start_date']).dt.days
    df['is_churned'] = df['cancellation_date'].notnull().astype(int)

    # Categorical Encoding
    df['is_monthly'] = (df['contract_type'] == 'Monthly').astype(int)
    df['is_basic'] = (df['plan_type'] == 'Basic').astype(int)
    df['is_karnataka'] = (df['State'] == 'Karnataka').astype(int)

    return df

class ChurnPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.feature_cols = ['monthly_charges', 'cltv', 'tenure_days', 'escalations', 
                             'complaint_count', 'avg_csat', 'is_monthly', 'is_basic', 'is_karnataka']
        self.is_trained = False
        self.metrics = {}

    def train(self):
        df = prepare_feature_dataset()
        X = df[self.feature_cols]
        y = df['is_churned']

        # Train model
        self.model.fit(X, y)
        self.is_trained = True

        y_pred = self.model.predict(X)
        self.metrics = {
            "accuracy": float(accuracy_score(y, y_pred)),
            "precision": float(precision_score(y, y_pred, zero_division=0)),
            "recall": float(recall_score(y, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y, y_pred, zero_division=0)),
            "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
            "feature_importances": dict(zip(self.feature_cols, self.model.feature_importances_.round(4).tolist()))
        }
        print(f"[+] ML Churn Prediction Model Trained Successfully (Accuracy: {self.metrics['accuracy']*100:.1f}%)")
        return self.metrics

    def predict_customer(self, customer_id):
        df = prepare_feature_dataset()
        cust_row = df[df['customerid'] == customer_id]
        if cust_row.empty:
            return None

        X_cust = cust_row[self.feature_cols]
        churn_prob = float(self.model.predict_proba(X_cust)[0][1])

        # Exact Risk Score calculation (0-100)
        row = cust_row.iloc[0]
        factor_score = 0
        factors = []

        if row['is_monthly'] == 1:
            factor_score += 25
            factors.append({"factor": "Monthly Contract Structure", "points": +25})
        if row['escalations'] >= 1:
            factor_score += 30
            factors.append({"factor": "Escalated Support Complaint", "points": +30})
        if row['is_basic'] == 1:
            factor_score += 15
            factors.append({"factor": "Basic Plan Tier Vulnerability", "points": +15})
        if row['is_karnataka'] == 1:
            factor_score += 15
            factors.append({"factor": "Karnataka Regional Price Friction", "points": +15})
        if row['tenure_days'] < 365:
            factor_score += 15
            factors.append({"factor": "Tenure < 1 Year", "points": +15})

        calculated_score = min(100, int((churn_prob * 50) + (factor_score * 0.5)))
        
        if calculated_score >= 70:
            risk_tier = "HIGH"
        elif calculated_score >= 40:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "LOW"

        return {
            "customerid": int(customer_id),
            "churn_probability": round(churn_prob * 100, 1),
            "risk_score": calculated_score,
            "risk_tier": risk_tier,
            "risk_factors": factors
        }

predictor = ChurnPredictor()

if __name__ == "__main__":
    predictor.train()
    print("Metrics:", predictor.metrics)
    print("Sample Customer #101 Risk Prediction:", predictor.predict_customer(101))
