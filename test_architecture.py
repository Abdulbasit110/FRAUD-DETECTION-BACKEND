#!/usr/bin/env python3
"""
Test script to verify the CustomerTransaction table and endpoints are working
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import CustomerTransaction, Transaction

# Create the app instance
app = create_app()

def test_database_setup():
    """Test if CustomerTransaction table was created properly"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Test CustomerTransaction table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'customer_transactions' in tables:
                print("✅ CustomerTransaction table exists")
                
                # Get table columns
                columns = [col['name'] for col in inspector.get_columns('customer_transactions')]
                print(f"✅ CustomerTransaction table has {len(columns)} columns")
                
                expected_columns = [
                    'id', 'customer_id', 'session_id', 'sending_date', 'mtn', 
                    'sender_id', 'sender_legal_name', 'prediction_confidence', 
                    'model_version', 'risk_score', 'created_at', 'updated_at'
                ]
                
                missing_columns = [col for col in expected_columns if col not in columns]
                if missing_columns:
                    print(f"⚠️  Missing columns: {missing_columns}")
                else:
                    print("✅ All expected columns present")
                    
            else:
                print("❌ CustomerTransaction table not found")
                
            # Test Transaction table (for training data)
            if 'transactions' in tables:
                print("✅ Transaction table exists (for training data)")
            else:
                print("❌ Transaction table not found")
                
        except Exception as e:
            print(f"❌ Database setup error: {str(e)}")

def test_model_imports():
    """Test if models can be imported properly"""
    try:
        from app.models import CustomerTransaction, Transaction, SenderFeatures
        print("✅ All models imported successfully")
        
        # Test model instantiation
        customer_txn = CustomerTransaction(
            customer_id="test_customer",
            sender_id="test_sender",
            total_sale=100.0
        )
        print("✅ CustomerTransaction model can be instantiated")
        
    except Exception as e:
        print(f"❌ Model import error: {str(e)}")

def test_routes_registered():
    """Test if routes are properly registered"""
    try:
        with app.app_context():
            # Get all registered routes
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(rule.rule)
            
            expected_routes = [
                '/customer-transactions/stats',
                '/customer-transactions',
                '/model/predict'
            ]
            
            for route in expected_routes:
                if any(route in r for r in routes):
                    print(f"✅ Route {route} is registered")
                else:
                    print(f"❌ Route {route} is missing")
                    
    except Exception as e:
        print(f"❌ Route registration error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Testing CustomerTransaction Architecture Setup...")
    print("=" * 50)
    
    test_model_imports()
    print()
    test_database_setup()
    print()
    test_routes_registered()
    
    print("=" * 50)
    print("✅ Architecture test completed!")
