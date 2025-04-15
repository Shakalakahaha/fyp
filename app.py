from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from flask_mail import Mail
from functools import wraps
import mysql.connector
import random
import string
import secrets
import os
import uuid
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import email_service
from model_initialization import initialize_system
from prediction_utils import process_prediction_request

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

@app.route('/logout')
def logout():
    """Log out the current user and redirect to login page."""
    # Clear the session
    session.clear()
    logger.info("User logged out successfully")
    return redirect(url_for('login'))

# Prediction endpoints
@app.route('/api/predict', methods=['POST'])
def predict_churn():
    """Predict churn using the selected model"""
    try:
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401

        # Get user info
        user_info = session['user']
        user_id = user_info['id']
        user_type = 'dev' if user_info.get('account_type') == 'developer' else 'user'
        logger.info(f"User type determined: {user_type} (account_type: {user_info.get('account_type')})")

        # Get form data
        prediction_name = request.form.get('prediction_name')
        model_id = request.form.get('model_id')

        logger.info(f"Received prediction request with model_id: {model_id} (type: {type(model_id)})")

        if not prediction_name or not model_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # Ensure model_id is a string
        try:
            model_id = str(model_id).strip()
            logger.info(f"Converted model_id to string: {model_id}")
        except Exception as e:
            logger.error(f"Error converting model_id to string: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Invalid model ID format: {model_id}'
            }), 400

        # Check if file was uploaded
        if 'dataset' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400

        file = request.files['dataset']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400

        # Check file extension
        allowed_extensions = {'.csv', '.xlsx', '.xls'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'message': 'Invalid file format. Only CSV and Excel files are allowed.'
            }), 400

        # Create directory if it doesn't exist
        upload_dir = os.path.join('datasets', user_type, 'uploadToPredict')
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{unique_id}_{safe_filename}"
        file_path = os.path.join(upload_dir, filename)

        # Save the file
        file.save(file_path)
        logger.info(f"File saved to {file_path}")

        # Get database connection
        conn = get_db_connection()

        # Process the prediction request
        result = process_prediction_request(
            file_path=file_path,
            model_id=model_id,
            prediction_name=prediction_name,
            user_type=user_type,
            user_id=user_id,
            conn=conn
        )

        conn.close()

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error in predict_churn: {str(e)}")

        # Check for scikit-learn version compatibility error
        error_message = str(e)
        if "No module named 'sklearn.ensemble._gb_losses'" in error_message or "Incompatible scikit-learn version" in error_message:
            return jsonify({
                'status': 'error',
                'message': "The selected model requires an older version of scikit-learn. Please try a different model or contact the administrator.",
                'details': "This model was created with scikit-learn 0.22.x but you're using a newer version."
            }), 400

        return jsonify({
            'status': 'error',
            'message': error_message
        }), 500

@app.route('/api/predictions/<int:prediction_id>/download')
def download_prediction(prediction_id):
    """Download prediction results"""
    try:
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401

        # Get user info
        user_info = session['user']
        user_id = user_info['id']
        user_type = 'dev' if user_info.get('account_type') == 'developer' else 'user'
        logger.info(f"User type determined for download: {user_type} (account_type: {user_info.get('account_type')})")

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get prediction info - handle both user and developer cases
        if user_type == 'dev':
            query = "SELECT * FROM predictions WHERE id = %s AND developer_id = %s"
        else:
            query = "SELECT * FROM predictions WHERE id = %s AND user_id = %s"

        logger.info(f"Executing query for {user_type} with ID {user_id}")
        cursor.execute(query, (prediction_id, user_id))
        prediction = cursor.fetchone()

        logger.info(f"Query result: {prediction is not None}")

        if not prediction:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Prediction not found or access denied'
            }), 404

        # Get the file path
        file_path = os.path.join('datasets', user_type, 'predictionResult', prediction['result_dataset_path'])
        logger.info(f"Looking for file at: {file_path}")

        if not os.path.exists(file_path):
            # Try alternative path formats
            alt_paths = [
                os.path.join('datasets', user_type, 'predictionResult', prediction['result_dataset_path']),
                prediction['result_dataset_path'],
                os.path.join('datasets', user_type, 'predictionResult', os.path.basename(prediction['result_dataset_path']))
            ]

            found = False
            for alt_path in alt_paths:
                logger.info(f"Trying alternative path: {alt_path}")
                if os.path.exists(alt_path):
                    file_path = alt_path
                    found = True
                    logger.info(f"Found file at: {file_path}")
                    break

            if not found:
                conn.close()
                return jsonify({
                    'status': 'error',
                    'message': 'Prediction file not found',
                    'details': f"Tried paths: {[file_path] + alt_paths}"
                }), 404

        conn.close()

        # Send the file
        download_name = os.path.basename(file_path)
        logger.info(f"Sending file: {file_path} with download name: {download_name}")

        return send_file(
            file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        logger.error(f"Error in download_prediction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/predictions/<int:prediction_id>/preview')
def preview_prediction(prediction_id):
    """Get a preview of prediction results (first 10 rows)"""
    try:
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401

        # Get user info
        user_info = session['user']
        user_id = user_info['id']
        user_type = 'dev' if user_info.get('account_type') == 'developer' else 'user'

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get prediction info - handle both user and developer cases
        if user_type == 'dev':
            query = "SELECT * FROM predictions WHERE id = %s AND developer_id = %s"
        else:
            query = "SELECT * FROM predictions WHERE id = %s AND user_id = %s"

        cursor.execute(query, (prediction_id, user_id))
        prediction = cursor.fetchone()

        if not prediction:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Prediction not found or access denied'
            }), 404

        # Get the file path
        file_path = os.path.join('datasets', user_type, 'predictionResult', prediction['result_dataset_path'])

        if not os.path.exists(file_path):
            # Try alternative path formats
            alt_paths = [
                os.path.join('datasets', user_type, 'predictionResult', prediction['result_dataset_path']),
                prediction['result_dataset_path'],
                os.path.join('datasets', user_type, 'predictionResult', os.path.basename(prediction['result_dataset_path']))
            ]

            found = False
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    file_path = alt_path
                    found = True
                    break

            if not found:
                conn.close()
                return jsonify({
                    'status': 'error',
                    'message': 'Prediction file not found'
                }), 404

        conn.close()

        # Read the CSV file
        import pandas as pd
        try:
            df = pd.read_csv(file_path)
            # Get first 10 rows
            preview_data = df.head(10).to_dict('records')
            return jsonify({
                'status': 'success',
                'preview': preview_data
            })
        except Exception as read_error:
            logger.error(f"Error reading CSV file: {str(read_error)}")
            return jsonify({
                'status': 'error',
                'message': f"Error reading prediction file: {str(read_error)}"
            }), 500

    except Exception as e:
        logger.error(f"Error in preview_prediction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/predictions/history')
def get_prediction_history():
    """Get prediction history for the current user"""
    try:
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401

        # Get user info
        user_info = session['user']
        user_id = user_info['id']
        user_type = 'dev' if user_info.get('account_type') == 'developer' else 'user'

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get prediction history - handle both user and developer cases
        if user_type == 'dev':
            query = """
            SELECT p.id, p.prediction_name, p.created_at, p.upload_dataset_path, p.result_dataset_path,
                   m.name as model_name, m.model_type_id,
                   JSON_EXTRACT(p.result, '$.churn_count') as churn_count,
                   JSON_EXTRACT(p.result, '$.no_churn_count') as no_churn_count,
                   JSON_EXTRACT(p.result, '$.churn_percentage') as churn_percentage,
                   JSON_EXTRACT(p.input_data, '$.total_records') as total_records
            FROM predictions p
            JOIN models m ON p.model_id = m.id
            WHERE p.developer_id = %s
            ORDER BY p.created_at DESC
            """
            cursor.execute(query, (user_id,))
        else:
            query = """
            SELECT p.id, p.prediction_name, p.created_at, p.upload_dataset_path, p.result_dataset_path,
                   m.name as model_name, m.model_type_id,
                   JSON_EXTRACT(p.result, '$.churn_count') as churn_count,
                   JSON_EXTRACT(p.result, '$.no_churn_count') as no_churn_count,
                   JSON_EXTRACT(p.result, '$.churn_percentage') as churn_percentage,
                   JSON_EXTRACT(p.input_data, '$.total_records') as total_records
            FROM predictions p
            JOIN models m ON p.model_id = m.id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
            """
            cursor.execute(query, (user_id,))

        predictions = cursor.fetchall()
        conn.close()

        # Process the results
        results = []
        for prediction in predictions:
            # Convert JSON strings to numbers
            churn_count = int(prediction['churn_count']) if prediction['churn_count'] else 0
            no_churn_count = int(prediction['no_churn_count']) if prediction['no_churn_count'] else 0
            churn_percentage = float(prediction['churn_percentage']) if prediction['churn_percentage'] else 0
            total_records = int(prediction['total_records']) if prediction['total_records'] else 0

            # Format the date
            created_at = prediction['created_at'].isoformat() if prediction['created_at'] else None

            # Map model_type_id to model_type string
            model_type_map = {
                1: 'Neural Network',
                2: 'Random Forest',
                3: 'Gradient Boosting',
                4: 'Logistic Regression',
                5: 'Decision Tree'
            }
            model_type = model_type_map.get(prediction['model_type_id'], 'Unknown')

            results.append({
                'id': prediction['id'],
                'prediction_name': prediction['prediction_name'],
                'model_name': prediction['model_name'],
                'model_type': model_type,
                'created_at': created_at,
                'total_records': total_records,
                'churn_distribution': {
                    'churn': churn_count,
                    'no_churn': no_churn_count,
                    'churn_rate': churn_percentage / 100 if churn_percentage else 0
                },
                'upload_dataset_path': prediction['upload_dataset_path'],
                'result_dataset_path': prediction['result_dataset_path'],
                'download_url': f"/api/predictions/{prediction['id']}/download",
                'upload_download_url': f"/api/predictions/{prediction['id']}/download-upload"
            })

        return jsonify({
            'status': 'success',
            'data': results
        })
    except Exception as e:
        logger.error(f"Error getting prediction history: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/predictions/<int:prediction_id>/feature-importance')
def get_prediction_feature_importance(prediction_id):
    """Get feature importance for a prediction"""
    try:
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401

        # Get user info
        user_info = session['user']
        user_id = user_info['id']
        user_type = 'dev' if user_info.get('account_type') == 'developer' else 'user'

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get prediction info - handle both user and developer cases
        if user_type == 'dev':
            query = "SELECT p.*, m.id as model_id, m.name as model_name, m.model_type_id FROM predictions p JOIN models m ON p.model_id = m.id WHERE p.id = %s AND p.developer_id = %s"
        else:
            query = "SELECT p.*, m.id as model_id, m.name as model_name, m.model_type_id FROM predictions p JOIN models m ON p.model_id = m.id WHERE p.id = %s AND p.user_id = %s"

        cursor.execute(query, (prediction_id, user_id))
        prediction = cursor.fetchone()

        if not prediction:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Prediction not found or access denied'
            }), 404

        # Get feature importance from the model
        model_id = prediction['model_id']

        # Map model_type_id to model_type string
        model_type_map = {
            1: 'Neural Network',
            2: 'Random Forest',
            3: 'Gradient Boosting',
            4: 'Logistic Regression',
            5: 'Decision Tree'
        }
        model_type = model_type_map.get(prediction['model_type_id'], 'Unknown')

        # Load the model
        from prediction_utils import load_model, get_feature_importance
        import pickle
        import os

        model_path = os.path.join('models', 'default_models', f"{model_type.lower().replace(' ', '_')}.pkl")
        feature_names_path = os.path.join('models', 'default_models', f"{model_type.lower().replace(' ', '_')}_features.pkl")

        if not os.path.exists(model_path) or not os.path.exists(feature_names_path):
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Model or feature names file not found'
            }), 404

        try:
            # Load model
            model = load_model(model_path)

            # Load feature names
            with open(feature_names_path, 'rb') as f:
                feature_names = pickle.load(f)

            # Get feature importance
            feature_importance = get_feature_importance(model, feature_names, None, None)

            conn.close()
            return jsonify({
                'status': 'success',
                'data': feature_importance
            })
        except Exception as e:
            logger.error(f"Error getting feature importance: {str(e)}")
            conn.close()
            return jsonify({
                'status': 'error',
                'message': f"Error getting feature importance: {str(e)}"
            }), 500

    except Exception as e:
        logger.error(f"Error in get_prediction_feature_importance: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/predictions/<int:prediction_id>/download-upload')
def download_upload_dataset(prediction_id):
    """Download the original uploaded dataset"""
    try:
        # Check if user is logged in
        if 'user' not in session:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated'
            }), 401

        # Get user info
        user_info = session['user']
        user_id = user_info['id']
        user_type = 'dev' if user_info.get('account_type') == 'developer' else 'user'

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get prediction info - handle both user and developer cases
        if user_type == 'dev':
            query = "SELECT * FROM predictions WHERE id = %s AND developer_id = %s"
        else:
            query = "SELECT * FROM predictions WHERE id = %s AND user_id = %s"

        cursor.execute(query, (prediction_id, user_id))
        prediction = cursor.fetchone()

        if not prediction:
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Prediction not found or access denied'
            }), 404

        # Get the file path
        file_path = os.path.join('datasets', user_type, 'uploadToPredict', prediction['upload_dataset_path'])

        if not os.path.exists(file_path):
            conn.close()
            return jsonify({
                'status': 'error',
                'message': 'Upload file not found'
            }), 404

        conn.close()

        # Send the file
        download_name = os.path.basename(file_path)
        return send_file(
            file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        logger.error(f"Error in download_upload_dataset: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/models/initialize', methods=['POST'])
@developer_required
def initialize_models():
    """Initialize default models and return their metrics."""
    try:
        result = initialize_system()
        return jsonify(result), 200 if result['status'] == 'success' else 500
    except Exception as e:
        logger.error(f"Error initializing models: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/models/metrics', methods=['GET'])
def get_models_metrics():
    """Get metrics for all models."""
    try:
        # Get user info from session
        user_info = session.get('user', {})
        company_id = user_info.get('company_id')

        if not company_id:
            return jsonify({
                'status': 'error',
                'message': 'User not authenticated or company ID not found'
            }), 401

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to get models with their metrics
        query = """
        SELECT m.id, m.name, mt.name as type, m.version, m.is_default,
               mm.accuracy, mm.precision as precision_val, mm.recall, mm.f1_score, mm.auc_roc,
               mm.additional_metrics
        FROM models m
        JOIN modeltypes mt ON m.model_type_id = mt.id
        JOIN modelmetrics mm ON m.id = mm.model_id
        WHERE m.company_id = %s OR m.is_default = 1
        ORDER BY m.is_default DESC, m.name ASC
        """

        cursor.execute(query, (company_id,))
        models_data = cursor.fetchall()

        # Format the data for the frontend
        models = []
        for model in models_data:
            # Initialize metrics dictionary with standard metrics
            metrics = {
                'Accuracy': float(model['accuracy']) if model['accuracy'] is not None else 0.0,
                'Precision': float(model['precision_val']) if model['precision_val'] is not None else 0.0,
                'Recall': float(model['recall']) if model['recall'] is not None else 0.0,
                'F1 Score': float(model['f1_score']) if model['f1_score'] is not None else 0.0,
                'AUC': float(model['auc_roc']) if model['auc_roc'] is not None else None
            }

            # Add additional metrics if available
            if model['additional_metrics']:
                try:
                    additional_metrics = json.loads(model['additional_metrics'])
                    if isinstance(additional_metrics, dict):
                        # If additional_metrics contains a 'metrics' key, use that
                        if 'metrics' in additional_metrics:
                            for key, value in additional_metrics['metrics'].items():
                                metrics[key] = float(value) if value is not None else 0.0
                        else:
                            # Otherwise use the additional_metrics directly
                            for key, value in additional_metrics.items():
                                metrics[key] = float(value) if value is not None else 0.0
                except Exception as e:
                    logger.warning(f"Error parsing additional metrics for model {model['id']}: {str(e)}")

            models.append({
                'id': model['id'],
                'name': model['name'],
                'type': model['type'],
                'version': model['version'],
                'is_default': bool(model['is_default']),
                'metrics': metrics
            })

        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'data': models
        }), 200
    except Exception as e:
        logger.error(f"Error getting model metrics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)