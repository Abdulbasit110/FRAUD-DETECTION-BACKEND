import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def send_email(recipient_email, subject, body, html_body=None):
    """
    Send an email to the specified recipient
    
    Args:
        recipient_email: Email address of the recipient
        subject: Subject of the email
        body: Plain text content of the email
        html_body: Optional HTML content of the email
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = recipient_email
        
        # Attach plain text and HTML versions
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
            
        # Connect to the SMTP server
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        
        # Send email
        server.sendmail(current_app.config['MAIL_USERNAME'], recipient_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_verification_code(email, code):
    """
    Send verification code email for password reset
    
    Args:
        email: Recipient's email address
        code: Verification code
        
    Returns:
        bool: True if the email was sent successfully
    """
    subject = "Your Password Reset Verification Code"
    
    # Plain text version
    body = f"""
    Hello,
    
    You recently requested to reset your password. Please use the following verification code to continue:
    
    {code}
    
    This code will expire in 15 minutes.
    
    If you didn't request this, please ignore this email.
    
    Thanks,
    Team FraudShield 
    """
    
    # HTML version
    html_body = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Password Reset Verification</h2>
        <p>Hello,</p>
        <p>You recently requested to reset your password. Please use the following verification code to continue:</p>
        <div style="background-color: #f4f4f4; padding: 10px; margin: 20px 0; text-align: center; font-size: 24px; letter-spacing: 5px;">
            <strong>{code}</strong>
        </div>
        <p>This code will expire in 15 minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
        <p>Thanks,<br>Your Application Team</p>
    </div>
    """
    
    return send_email(email, subject, body, html_body)
