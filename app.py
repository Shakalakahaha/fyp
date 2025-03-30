from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_mail import Mail
from functools import wraps
import mysql.connector
import random
import string
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import email_service
from model_initialization import initialize_default_models, get_model_metrics, initialize_developer_environment

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Developer only decorator
def developer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('account_type') != 'developer':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# User only decorator
def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('account_type') != 'user':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Email Configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='02cheeyongng@gmail.com',
    MAIL_PASSWORD='qimfvdplgqmnuqyh',
    MAIL_DEFAULT_SENDER='02cheeyongng@gmail.com',
    MAIL_MAX_EMAILS=None,
    MAIL_ASCII_ATTACHMENTS=False,
    MAIL_DEBUG=True
)

mail = Mail(app)

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="fyp_db"
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

# Generate a unique company ID starting with CCP
def generate_company_id(cursor):
    while True:
        # Generate a random 7-digit number
        random_digits = ''.join(random.choices(string.digits, k=7))
        # Combine with CCP prefix
        company_id = f"CCP{random_digits}"
        
        # Check if it exists in the database
        cursor.execute("SELECT COUNT(*) FROM Companies WHERE id = %s", (company_id,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            return company_id

# Routes for pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register-company')
def register_company():
    return render_template('register_company.html')

@app.route('/register-user')
def register_user():
    return render_template('register_user.html')

# API Routes for AJAX calls

# Company Registration
@app.route('/api/register-company', methods=['POST'])
def api_register_company():
    data = request.json
    company_name = data.get('company_name')
    company_email = data.get('company_email')
    
    if not company_name or not company_email:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Check if company already exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Companies WHERE email = %s", (company_email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Company with this email already exists"}), 400
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Store company info in session for verification
    session['pending_company'] = {
        'name': company_name,
        'email': company_email,
        'verification_token': verification_token
    }
    
    try:
        # Send verification email
        token, verification_code = email_service.send_company_verification_email(company_email, company_name, verification_token)
        
        # Update token with the actual numeric code that was sent
        session['pending_company']['verification_token'] = token
        session['pending_company']['verification_code'] = verification_code
        
        logger.info(f"Verification email sent to {company_email}, code: {verification_code}")
        print(f"Verification code for {company_email}: {verification_code}")
        return jsonify({"success": True, "message": "Verification email sent"})
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/verify-company', methods=['POST'])
def api_verify_company():
    data = request.json
    token = data.get('token')
    
    if not session.get('pending_company'):
        logger.error("No pending company registration found in session")
        return jsonify({"success": False, "message": "No pending company registration found"}), 400
    
    # Get verification code from session
    verification_code = session['pending_company'].get('verification_code')
    
    logger.info(f"Company verification attempt - Entered: {token}, Expected: {verification_code}")
    
    # Check if token matches the verification code
    if token != verification_code:
        logger.warning(f"Invalid verification code entered: {token}")
        return jsonify({"success": False, "message": "Invalid verification code"}), 400
    
    # Register company in database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        company_id = generate_company_id(cursor)
        
        # Insert into Companies table
        cursor.execute(
            "INSERT INTO Companies (id, name, email, email_verified) VALUES (%s, %s, %s, %s)",
            (company_id, session['pending_company']['name'], session['pending_company']['email'], True)
        )
        
        conn.commit()
        
        # Clear session data
        company_email = session['pending_company']['email']
        del session['pending_company']
        
        logger.info(f"Company registered successfully: {company_email}, ID: {company_id}")
        return jsonify({"success": True, "message": "Registration successful", "company_id": company_id})
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error during company registration: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# User/Developer Registration
@app.route('/api/register-user', methods=['POST'])
def api_register_user():
    data = request.json
    account_type = data.get('account_type')
    company_id = data.get('company_id')
    email = data.get('email')
    password = data.get('password')
    
    if not company_id or not email or not password:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Check if user already exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if account_type == 'developer':
        cursor.execute("SELECT * FROM Developers WHERE email = %s", (email,))
    else:
        cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "User with this email already exists"}), 400
    
    # Check if company exists
    cursor.execute("SELECT * FROM Companies WHERE id = %s", (company_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "Invalid company ID"}), 400
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Hash password
    hashed_password = generate_password_hash(password)
    
    # Store user info in session for verification
    session['pending_user'] = {
        'account_type': account_type,
        'company_id': company_id,
        'email': email,
        'password': hashed_password,
        'verification_token': verification_token
    }
    
    try:
        # Send verification email
        if account_type == 'developer':
            token, verification_code = email_service.send_developer_verification_email(email, company_id, verification_token)
        else:
            token, verification_code = email_service.send_user_verification_email(email, company_id, verification_token)
        
        # Update token with the actual numeric code that was sent
        session['pending_user']['verification_token'] = token
        session['pending_user']['verification_code'] = verification_code
        
        logger.info(f"Verification email sent to {email}, code: {verification_code}")
        print(f"Verification code for {email}: {verification_code}")
        return jsonify({"success": True, "message": "Verification email sent"})
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/verify-user', methods=['POST'])
def api_verify_user():
    data = request.json
    token = data.get('token')
    
    if not session.get('pending_user'):
        logger.error("No pending user registration found in session")
        return jsonify({"success": False, "message": "No pending user registration found"}), 400
    
    # Get verification code from session
    verification_code = session['pending_user'].get('verification_code')
    
    logger.info(f"User verification attempt - Entered: {token}, Expected: {verification_code}")
    
    # Check if token matches the verification code
    if token != verification_code:
        logger.warning(f"Invalid verification code entered: {token}")
        return jsonify({"success": False, "message": "Invalid verification code"}), 400
    
    # Register user in database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if session['pending_user']['account_type'] == 'developer':
            cursor.execute(
                "INSERT INTO Developers (company_id, email, password_hash, email_verified) VALUES (%s, %s, %s, %s)",
                (session['pending_user']['company_id'], session['pending_user']['email'], 
                 session['pending_user']['password'], True)
            )
        else:
            cursor.execute(
                "INSERT INTO Users (company_id, email, password_hash, email_verified) VALUES (%s, %s, %s, %s)",
                (session['pending_user']['company_id'], session['pending_user']['email'], 
                 session['pending_user']['password'], True)
            )
        
        conn.commit()
        
        # Clear session data
        user_email = session['pending_user']['email']
        del session['pending_user']
        
        logger.info(f"User registered successfully: {user_email}")
        return jsonify({"success": True, "message": "Registration successful"})
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error during user registration: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Login
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    account_type = data.get('account_type')
    email = data.get('email')
    password = data.get('password')
    
    logger.info(f"Login attempt - Type: {account_type}, Email: {email}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if account_type == 'developer':
            cursor.execute("SELECT * FROM Developers WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM Users WHERE email = %s", (email,))
        
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Store user info in session
            session['user'] = {
                'id': user['id'],
                'email': user['email'],
                'account_type': account_type,
                'company_id': user['company_id']
            }
            
            logger.info(f"Login successful: {email}")
            return jsonify({"success": True, "message": "Login successful"})
        else:
            logger.warning(f"Login failed - Invalid credentials: {email}")
            return jsonify({"success": False, "message": "Invalid email or password"}), 401
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Password Recovery
@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.json
    email = data.get('email')
    account_type = data.get('account_type')
    
    logger.info(f"Password reset attempt for {account_type}: {email}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if user/developer exists with given email
        if account_type == 'user':
            cursor.execute("SELECT email FROM Users WHERE email = %s", (email,))
        elif account_type == 'developer':
            cursor.execute("SELECT email FROM Developers WHERE email = %s", (email,))
        else:
            logger.warning(f"Invalid account type: {account_type}")
            return jsonify({"success": False, "message": "Invalid account type"}), 400
        
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Password reset failed - {account_type} not found: {email}")
            return jsonify({"success": False, "message": f"No {account_type} found with this email"}), 404
        
        # Generate a reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Generate a 6-digit numeric code
        verification_code = email_service.generate_numeric_code()
        
        # Send reset email WITH the verification code
        token, sent_code = email_service.send_forgot_password_email(email, account_type, reset_token)
        
        # IMPORTANT: Use the code that was ACTUALLY SENT in the email
        # Store the code that was sent in the session
        session['password_reset'] = {
            'email': email,
            'account_type': account_type,
            'reset_token': reset_token,
            'verification_code': sent_code  # Use the code returned from the email service
        }
        
        # Log the code for debugging
        logger.info(f"Password reset verification code for {email}: {sent_code}")
        print(f"Password reset code sent to {email}: {sent_code}")
        
        return jsonify({"success": True, "message": "Password reset email sent"})
    except Exception as e:
        logger.error(f"Error during password reset attempt: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/verify-reset-token', methods=['POST'])
def api_verify_reset_token():
    data = request.json
    token = data.get('token')
    
    # Simple log
    logger.info(f"Password reset verification attempt with token: {token}")
    
    if not session.get('password_reset'):
        logger.error("No password reset in progress")
        return jsonify({"success": False, "message": "No password reset in progress"}), 400
    
    # Get the verification code from session
    verification_code = session['password_reset']['verification_code']
    
    logger.info(f"Password reset verification attempt - Entered: {token}, Expected: {verification_code}")
    
    # Check if token matches the verification code (simple equality check)
    if token != verification_code:
        logger.warning(f"Invalid password reset verification code entered: {token}")
        return jsonify({"success": False, "message": "Invalid verification code"}), 400
    
    # Success case
    logger.info(f"Password reset verification successful for: {session['password_reset']['email']}")
    return jsonify({"success": True, "message": "Token verified successfully"})

@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    data = request.json
    new_password = data.get('new_password')
    
    if not session.get('password_reset'):
        logger.error("No password reset in progress")
        return jsonify({"success": False, "message": "No password reset in progress"}), 400
    
    # Get user data from session
    email = session['password_reset']['email']
    account_type = session['password_reset']['account_type']
    
    # Hash the new password
    hashed_password = generate_password_hash(new_password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update password in appropriate table based on account type
        if account_type == 'user':
            cursor.execute("UPDATE Users SET password_hash = %s WHERE email = %s", (hashed_password, email))
        elif account_type == 'developer':
            cursor.execute("UPDATE Developers SET password_hash = %s WHERE email = %s", (hashed_password, email))
        else:
            logger.error(f"Invalid account type during password reset: {account_type}")
            return jsonify({"success": False, "message": "Invalid account type"}), 400
        
        conn.commit()
        
        # Clear session data
        del session['password_reset']
        
        logger.info(f"Password reset successful for {account_type}: {email}")
        return jsonify({"success": True, "message": "Password reset successful"})
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during password reset: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Company ID Recovery
@app.route('/api/recover-company-id', methods=['POST'])
def api_recover_company_id():
    data = request.json
    email = data.get('email')
    
    logger.info(f"Company ID recovery attempt for: {email}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # First check if it's a company email
        cursor.execute("SELECT id FROM Companies WHERE email = %s", (email,))
        company = cursor.fetchone()
        
        if company:
            # Direct match with company email
            company_id = company['id']
            
            # For direct match, generate a recovery token too
            recovery_token = secrets.token_urlsafe(32)
            verification_code = email_service.generate_numeric_code()
            
            # Store in session
            session['company_id_recovery'] = {
                'email': email,
                'recovery_token': recovery_token,
                'verification_code': verification_code,
                'company_id': company_id
            }
            
            # Send the numeric verification code via email
            token, code = email_service.send_forgot_company_id_email(email, company_id, verification_code)
            
            logger.info(f"Company ID recovery verification code sent to: {email}")
            return jsonify({"success": True, "message": "Verification code sent to email", "direct_match": False})
        else:
            # Check if it's a developer or user email
            cursor.execute("SELECT company_id FROM Developers WHERE email = %s", (email,))
            developer = cursor.fetchone()
            
            if developer:
                company_id = developer['company_id']
            else:
                cursor.execute("SELECT company_id FROM Users WHERE email = %s", (email,))
                user = cursor.fetchone()
                
                if user:
                    company_id = user['company_id']
                else:
                    logger.warning(f"Company ID recovery failed - Email not associated with any company: {email}")
                    return jsonify({"success": False, "message": "Email not associated with any company"}), 404
            
            # For developer/user, generate a recovery token
            recovery_token = secrets.token_urlsafe(32)
            verification_code = email_service.generate_numeric_code()
            
            # Store in session
            session['company_id_recovery'] = {
                'email': email,
                'recovery_token': recovery_token,
                'verification_code': verification_code,
                'company_id': company_id
            }
            
            # Send the numeric verification code via email
            token, code = email_service.send_forgot_company_id_email(email, company_id, verification_code)
            
            logger.info(f"Company ID recovery verification code sent to {email}, ID: {company_id}")
            print(f"Company ID recovery code for {email}: {verification_code}")
            return jsonify({"success": True, "message": "Verification code sent to email", "direct_match": False})
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during company ID recovery: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/verify-company-id-recovery', methods=['POST'])
def api_verify_company_id_recovery():
    data = request.json
    token = data.get('token')
    
    if not session.get('company_id_recovery'):
        logger.error("No company ID recovery in progress")
        return jsonify({"success": False, "message": "No company ID recovery in progress"}), 400
    
    # Get the verification code from session
    verification_code = session['company_id_recovery']['verification_code']
    
    logger.info(f"Company ID recovery verification attempt - Entered: {token}, Expected: {verification_code}")
    
    # Check if token matches the verification code
    if token != verification_code:
        logger.warning(f"Invalid company ID recovery verification code entered: {token}")
        return jsonify({"success": False, "message": "Invalid recovery code"}), 400
    
    # Return company ID
    company_id = session['company_id_recovery']['company_id']
    
    # Clear session
    email = session['company_id_recovery']['email']
    del session['company_id_recovery']
    
    logger.info(f"Company ID recovery verified for: {email}, ID: {company_id}")
    return jsonify({"success": True, "company_id": company_id})

# Dashboard routes
@app.route('/dev_dashboard')
@developer_required
def developer_dashboard():
    return render_template('dev_dashboard.html')

@app.route('/user_dashboard')
@user_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/dev/dashboard')
@developer_required
def dev_dashboard():
    """Render the developer dashboard."""
    return render_template('dev_dashboard.html')

@app.route('/api/models/initialize', methods=['POST'])
@developer_required
def initialize_models():
    """Initialize default models and return their metrics."""
    try:
        # Get developer ID from session
        developer_id = session['user']['id']
        
        result = initialize_developer_environment(developer_id)
        return jsonify(result), 200 if result['status'] == 'success' else 500
    except Exception as e:
        logger.error(f"Error initializing models: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/models/metrics', methods=['GET'])
@developer_required
def get_models_metrics():
    """Get metrics for all models."""
    try:
        # Get developer ID from session
        developer_id = session['user']['id']
        
        metrics = get_model_metrics(developer_id)
        return jsonify({
            'status': 'success',
            'data': metrics
        }), 200
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)