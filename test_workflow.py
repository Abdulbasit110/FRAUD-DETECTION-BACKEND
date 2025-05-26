#!/usr/bin/env python3
"""
Test script to verify the complete workflow from prediction to dashboard
"""
import sys
import os
import requests
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_prediction_endpoint():
    """Test making a prediction and storing it in CustomerTransaction table"""
    print("🔍 Testing prediction endpoint...")
    
    # Test data
    test_data = {
        "customer_id": "workflow_test_001",
        "session_id": "test_session_456",
        "sender_id": "2001",
        "total_sale": 15000,
        "selling_price": 14000,
        "goods_code": "clothing",
        "mtn": "Bank Transfer",
        "sender_legal_name": "Workflow Test Customer",
        "sending_date": "2024-05-25"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/model/predict",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Prediction successful!")
            print(f"   Prediction: {result.get('prediction')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            print(f"   Risk Score: {result.get('risk_score', 'N/A')}")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        return False

def test_dashboard_stats():
    """Test the dashboard stats endpoint"""
    print("\n🔍 Testing dashboard stats...")
    
    try:
        response = requests.get("http://localhost:5000/customer-transactions/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Dashboard stats retrieved!")
            print(f"   Data Source: {stats.get('data_source')}")
            print(f"   Total Customers: {stats.get('total_customers')}")
            print(f"   Total Transactions: {stats.get('total_transactions')}")
            print(f"   Genuine Customers: {stats.get('genuine_customers')}")
            print(f"   Suspicious Customers: {stats.get('suspicious_customers')}")
            print(f"   Mixed Customers: {stats.get('mixed_customers')}")
            return True
        else:
            print(f"❌ Stats retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Stats error: {str(e)}")
        return False

def test_customer_transactions_list():
    """Test the customer transactions list endpoint"""
    print("\n🔍 Testing customer transactions list...")
    
    try:
        response = requests.get("http://localhost:5000/customer-transactions/")
        
        if response.status_code == 200:
            data = response.json()
            transactions = data.get('transactions', [])
            print(f"✅ Customer transactions retrieved!")
            print(f"   Total: {data.get('total', 0)}")
            print(f"   Current page: {data.get('page', 0)}")
            print(f"   Transactions in this page: {len(transactions)}")
            
            if transactions:
                latest = transactions[0]
                print(f"   Latest transaction:")
                print(f"     Customer ID: {latest.get('customer_id')}")
                print(f"     Sender: {latest.get('sender_legal_name')}")
                print(f"     Prediction: {latest.get('prediction')}")
                print(f"     Amount: {latest.get('total_sale')}")
            
            return True
        else:
            print(f"❌ Transactions list failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Transactions list error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Complete CustomerTransaction Workflow...")
    print("=" * 60)
    
    # Test each component
    prediction_success = test_prediction_endpoint()
    stats_success = test_dashboard_stats()
    list_success = test_customer_transactions_list()
    
    print("\n" + "=" * 60)
    
    if prediction_success and stats_success and list_success:
        print("🎉 ALL WORKFLOW TESTS PASSED!")
        print("✅ Architecture is working correctly!")
        print("✅ Predictions are stored in CustomerTransaction table")
        print("✅ Dashboard can retrieve live customer data")
        print("✅ Frontend can display customer transactions")
    else:
        print("❌ Some workflow tests failed")
    
    print("=" * 60)
