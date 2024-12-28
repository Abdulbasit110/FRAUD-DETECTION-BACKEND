# Fraud Detection System Backend

This repository implements the backend for a fraud detection system built with Flask. It provides APIs for transaction data management, user authentication, and fraud detection. The system is designed to integrate with a frontend interface for real-time monitoring and analysis.

## Features

- **Fraud Detection**:
  - Upload transaction data via CSV.
  - Process transactions and run fraud detection models.

- **User Management**:
  - User authentication with sign-up, login, password reset, and forgot password features.

- **Database Management**:
  - PostgreSQL integration with SQLAlchemy ORM.
  - Flask-Migrate for database schema management.

- **Frontend Integration**:
  - APIs are designed to work with a frontend interface for real-time visualization and reporting.

## Endpoints

### **Transactions**
- `/transactions/upload` (POST): Upload a CSV file containing transactions.
- `/transactions/upload-local` (POST): Upload transactions from a local CSV file path.
- **(Future)** Fraud detection endpoints for running models and fetching results.

### **Authentication**
- `/auth/signup` (POST): Register a new user.
- `/auth/login` (POST): Log in an existing user.
- `/auth/forgot-password` (POST): Reset password via email.
- `/auth/reset-password` (POST): Reset password with old and new credentials.

### **Users**
- `/users` (GET): Retrieve a list of all registered users.

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Abdulbasit110/FRAUD-DETECTION-BACKEND.git
   cd your-repo-name
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Linux/Mac
   venv\Scripts\activate     # For Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following content:
   ```plaintext
   DATABASE_URI=postgresql://<username>:<password>@<host>/<database>
   FLASK_APP=run.py
   FLASK_ENV=development
   ```

5. Run database migrations:
   ```bash
   flask db upgrade
   ```

6. Start the development server:
   ```bash
   flask run
   ```

## Project Structure

```plaintext
.
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models.py            # Database models
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── transactions.py  # Transaction routes
│   ├── utils/
│   │   ├── helpers.py       # Helper functions for data validation
├── fraud_detection/         # Fraud detection model logic (future extension)
│   ├── model.py             # Placeholder for fraud detection model integration
├── migrations/              # Flask-Migrate migration files
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point for the Flask application
└── README.md                # Documentation
```

## Future Enhancements

- **Fraud Detection**:
  - Integrate a machine learning model for identifying fraudulent transactions.
  - Add endpoints to fetch fraud detection results.

- **Frontend Integration**:
  - Design APIs for interactive dashboards and real-time monitoring.

- **Additional Features**:
  - Support for role-based access control (RBAC) for enhanced security.
  - Advanced data analytics for transaction insights.

## Contributions

Contributions are welcome! Feel free to open issues or submit pull requests for new features, bug fixes, or improvements.

