from flask import Flask, render_template
from flask_mail import Mail, Message
import secrets
import logging
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and Mail
app = Flask(__name__)

# Email Configuration from your image
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='02cheeyongng@gmail.com',
    MAIL_PASSWORD='qimfvdplgqmnuqyh',  # Note: Using app passwords is more secure
    MAIL_DEFAULT_SENDER='02cheeyongng@gmail.com',
    MAIL_MAX_EMAILS=None,
    MAIL_ASCII_ATTACHMENTS=False,
    MAIL_DEBUG=True
)

mail = Mail(app)

def log_email_attempt(recipient, subject, success=True):
    """Log email sending attempts for debugging"""
    if success:
        logger.info(f"Email sent - To: {recipient}, Subject: {subject}")
    else:
        logger.error(f"Email failed - To: {recipient}, Subject: {subject}")
    # Also print to console for immediate visibility
    print(f"{'✓' if success else '✗'} Email {'sent to' if success else 'failed for'} {recipient}: {subject}")

def generate_token():
    """Generate a secure random token for verification or password reset"""
    return secrets.token_urlsafe(32)

def generate_numeric_code(length=6):
    """Generate a numeric-only verification code of specified length"""
    return ''.join(random.choices('0123456789', k=length))

def send_company_verification_email(email, company_name, token):
    """Send a verification email for company registration"""
    try:
        msg = Message(
            subject="Verify Your Company Registration",
            recipients=[email]
        )
        
        # Generate numeric verification code (6 digits)
        verification_code = generate_numeric_code()
        
        msg.html = f"""
        <h1>Company Registration Verification</h1>
        <p>Dear {company_name},</p>
        <p>Thank you for registering your company with our system.</p>
        <p>Your verification code is: <strong>{verification_code}</strong></p>
        <p>Enter this code in the verification page to complete your registration.</p>
        <p>This code will expire in 24 hours.</p>
        <p>If you did not register for this service, please ignore this email.</p>
        <p>Best regards,<br>Support Team</p>
        """
        
        mail.send(msg)
        log_email_attempt(email, "Verify Your Company Registration")
        # Return both the token and the numeric code
        return token, verification_code
    except Exception as e:
        log_email_attempt(email, "Verify Your Company Registration", False)
        logger.error(f"Failed to send company verification email: {str(e)}")
        raise

def send_developer_verification_email(email, company_id, token):
    """Send a verification email for developer registration"""
    try:
        msg = Message(
            subject="Verify Your Developer Account",
            recipients=[email]
        )
        
        # Generate numeric verification code (6 digits)
        verification_code = generate_numeric_code()
        
        msg.html = f"""
        <h1>Developer Account Verification</h1>
        <p>Dear Developer,</p>
        <p>Thank you for registering as a developer for company ID: {company_id}.</p>
        <p>Your verification code is: <strong>{verification_code}</strong></p>
        <p>Enter this code in the verification page to complete your registration.</p>
        <p>This code will expire in 24 hours.</p>
        <p>If you did not register for this service, please ignore this email.</p>
        <p>Best regards,<br>Support Team</p>
        """
        
        mail.send(msg)
        log_email_attempt(email, "Verify Your Developer Account")
        # Return both the token and the numeric code
        return token, verification_code
    except Exception as e:
        log_email_attempt(email, "Verify Your Developer Account", False)
        logger.error(f"Failed to send developer verification email: {str(e)}")
        raise

def send_user_verification_email(email, company_id, token):
    """Send a verification email for user registration"""
    try:
        msg = Message(
            subject="Verify Your User Account",
            recipients=[email]
        )
        
        # Generate numeric verification code (6 digits)
        verification_code = generate_numeric_code()
        
        msg.html = f"""
        <h1>User Account Verification</h1>
        <p>Dear User,</p>
        <p>Thank you for registering as a user for company ID: {company_id}.</p>
        <p>Your verification code is: <strong>{verification_code}</strong></p>
        <p>Enter this code in the verification page to complete your registration.</p>
        <p>This code will expire in 24 hours.</p>
        <p>If you did not register for this service, please ignore this email.</p>
        <p>Best regards,<br>Support Team</p>
        """
        
        mail.send(msg)
        log_email_attempt(email, "Verify Your User Account")
        # Return both the token and the numeric code
        return token, verification_code
    except Exception as e:
        log_email_attempt(email, "Verify Your User Account", False)
        logger.error(f"Failed to send user verification email: {str(e)}")
        raise

def send_forgot_password_email(email, user_type, token):
    """Send a password reset email for users or developers"""
    try:
        msg = Message(
            subject="Password Reset Request",
            recipients=[email]
        )
        
        # Generate numeric verification code (6 digits)
        verification_code = generate_numeric_code()
        
        msg.html = f"""
        <h1>Password Reset Request</h1>
        <p>Dear {user_type.capitalize()},</p>
        <p>We received a request to reset your password.</p>
        <p>Your verification code is: <strong>{verification_code}</strong></p>
        <p>Enter this code in the reset password page to continue.</p>
        <p>This code will expire in 1 hour.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>Best regards,<br>Support Team</p>
        """
        
        mail.send(msg)
        log_email_attempt(email, "Password Reset Request")
        
        # Print verification code for debugging
        print(f"Sending verification code: {verification_code} Type: {type(verification_code)}")
        
        # Return both the token and the numeric code
        return token, verification_code
    except Exception as e:
        log_email_attempt(email, "Password Reset Request", False)
        logger.error(f"Failed to send password reset email: {str(e)}")
        raise

def send_forgot_company_id_email(email, company_id, verification_code=None):
    """Send an email with the recovered company ID verification code"""
    try:
        # Generate a token for verification
        token = generate_token()
        
        msg = Message(
            subject="Company ID Recovery",
            recipients=[email]
        )
        
        if verification_code:
            # Send verification code email
            msg.html = f"""
            <h1>Company ID Recovery</h1>
            <p>Dear User,</p>
            <p>We received a request to recover your company ID.</p>
            <p>Your verification code is: <strong>{verification_code}</strong></p>
            <p>Enter this code to complete the recovery process and view your company ID.</p>
            <p>If you did not request this information, please ignore this email.</p>
            <p>Best regards,<br>Support Team</p>
            """
        else:
            # Send direct company ID email
            msg.html = f"""
            <h1>Company ID Recovery</h1>
            <p>Dear User,</p>
            <p>We received a request to recover your company ID.</p>
            <p>Your company ID is: <strong>{company_id}</strong></p>
            <p>If you did not request this information, please secure your account.</p>
            <p>Best regards,<br>Support Team</p>
            """
        
        mail.send(msg)
        log_email_attempt(email, "Company ID Recovery")
        
        # Return both the token and the verification code (only 2 values)
        return token, verification_code
    except Exception as e:
        log_email_attempt(email, "Company ID Recovery", False)
        logger.error(f"Failed to send company ID recovery email: {str(e)}")
        raise

# Function to test the email sending capability
def test_email_service():
    try:
        test_email = input("Enter an email to test the service: ")
        test_message = Message(
            subject="Test Email from Flask Company System",
            recipients=[test_email],
            body="This is a test email to verify that the email service is working correctly."
        )
        mail.send(test_message)
        log_email_attempt(test_email, "Test Email from Flask Company System")
        print(f"Test email sent to {test_email}")
        return True
    except Exception as e:
        log_email_attempt(test_email, "Test Email from Flask Company System", False)
        print(f"Error sending test email: {e}")
        logger.error(f"Error in test_email_service: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        print("Testing email service...")
        test_email_service() 