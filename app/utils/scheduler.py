import requests
import random
import string
import logging
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.base import SchedulerNotRunningError

logger = logging.getLogger(__name__)

def generate_random_transaction():
    """Generate random transaction data for testing"""
    
    # Generate a random sender ID (either reuse an existing one or create a new one)
    sender_id = f"TEST{random.randint(1000, 9999)}"
    
    # Generate random amounts between $100 and $5000
    amount = round(random.uniform(100, 5000), 2)
    
    # Random date within the last 30 days
    sending_date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
    
    # Create the transaction payload
    transaction = {
        "user_id": "1",  # Default test user ID
        "sending_date": sending_date,
        "mtn": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        "sender_id": sender_id,
        "sender_legal_name": f"Test Sender {sender_id}",
        "channel": random.choice(["APP", "WEB", "AGENT"]),
        "payer_rep_code": ''.join(random.choices(string.ascii_uppercase, k=4)),
        "sender_country": random.choice(["US", "UK", "CA", "AU"]),
        "sender_status": "ACTIVE",
        "sender_date_of_birth": "1980-01-01",
        "sender_email": f"sender{sender_id}@example.com",
        "sender_mobile": f"+1{random.randint(1000000000, 9999999999)}",
        "sender_phone": f"+1{random.randint(1000000000, 9999999999)}",
        "beneficiary_client_id": f"BEN{random.randint(1000, 9999)}",
        "beneficiary_name": f"Beneficiary {random.randint(1000, 9999)}",
        "beneficiary_first_name": f"First{random.randint(100, 999)}",
        "beneficiary_country": random.choice(["IN", "PK", "BD", "NG"]),
        "beneficiary_email": f"beneficiary{random.randint(1000, 9999)}@example.com",
        "beneficiary_mobile": f"+91{random.randint(1000000000, 9999999999)}",
        "beneficiary_phone": f"+91{random.randint(1000000000, 9999999999)}",
        "sending_country": random.choice(["US", "UK", "CA", "AU"]),
        "payout_country": random.choice(["IN", "PK", "BD", "NG"]),
        "total_sale": amount,
        "sending_currency": random.choice(["USD", "GBP", "CAD", "AUD"]),
        "payment_method": random.choice(["CARD", "BANK", "CASH"]),
        "compliance_release_date": (datetime.now() - timedelta(days=random.randint(0, 10))).strftime("%Y-%m-%d")
    }
    
    return transaction

def send_test_transaction():
    """Send a randomly generated transaction to the predict endpoint"""
    try:
        # Generate random transaction data
        transaction = generate_random_transaction()
        
        # Determine if this should be a suspicious transaction (10% chance)
        is_suspicious = random.random() < 0.1
        
        # If suspicious, modify some fields to make it more likely to be flagged
        if is_suspicious:
            # Increase the amount significantly
            transaction["total_sale"] = round(random.uniform(8000, 15000), 2)
            
            # Create a new sender ID to ensure it's a first-time sender
            transaction["sender_id"] = f"NEW{random.randint(10000, 99999)}"
        
        # Log the transaction we're sending
        logger.info(f"Sending test transaction. Sender: {transaction['sender_id']}, Amount: {transaction['total_sale']}")
        
        # Make the API call to the predict endpoint
        response = requests.post(
            "http://localhost:5000/model/predict",
            json=transaction,
            headers={"Content-Type": "application/json"}
        )
        
        # Log the response
        if response.status_code == 201:
            result = response.json()
            logger.info(f"Transaction processed successfully. Prediction: {result.get('predicted_label')}, Confidence: {result.get('confidence')}")
        else:
            logger.error(f"Failed to process transaction. Status code: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending test transaction: {str(e)}")

def init_scheduler(app):
    """Initialize and start the scheduler"""
    scheduler = BackgroundScheduler()
    
    # Add the job to run every 5 minutes (adjustable)
    scheduler.add_job(
        send_test_transaction,
        IntervalTrigger(minutes=5),
        id='test_transaction_job',
        name='Send test transaction to prediction endpoint',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduled job initialized to send test transactions every 5 minutes")
    
    # Add scheduler to app context for proper shutdown
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    app.extensions['scheduler'] = scheduler
    
    # Shut down the scheduler when the app is shutting down
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if 'scheduler' in app.extensions:
            scheduler = app.extensions['scheduler']
            try:
                if scheduler.running:
                    scheduler.shutdown()
                    logger.info("Scheduler has been shut down successfully")
            except SchedulerNotRunningError:
                logger.info("Scheduler was already shut down")
            except Exception as e:
                logger.error(f"Error shutting down scheduler: {str(e)}")