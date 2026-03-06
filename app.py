from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
from werkzeug.utils import secure_filename
from predictor import LungCancerPredictor
import json
from dotenv import load_dotenv
import random
import time
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize predictor
predictor = LungCancerPredictor()

# User database (in production, use a proper database)
USERS_DB = {
    'rakshith': {
        'password': 'Rakshith@21',
        'mobile': '+91-9390175239',
        'email': 'rakshith@medicalai.com',
        'full_name': 'Dr. Rakshith',
        'user_type': 'primary'
    }
}

# OTP storage (in production, use Redis or database)
OTP_STORAGE = {}

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_sms(mobile_number, otp):
    """
    Simulate sending OTP via SMS
    In production, integrate with SMS service like Twilio, AWS SNS, etc.
    """
    print(f"📱 SMS Sent to {mobile_number}: Your OTP is {otp}")
    print(f"🔐 Demo OTP Code: {otp}")
    print(f"📞 Mobile: {mobile_number}")
    print("=" * 50)
    # For demo purposes, we'll just print the OTP
    # In production, replace this with actual SMS API call
    return True
    return True

def is_otp_valid(mobile_number, entered_otp):
    """Check if OTP is valid and not expired"""
    if mobile_number not in OTP_STORAGE:
        return False
    
    stored_data = OTP_STORAGE[mobile_number]
    stored_otp = stored_data['otp']
    timestamp = stored_data['timestamp']
    
    # Check if OTP is expired (5 minutes)
    if datetime.now() - timestamp > timedelta(minutes=5):
        del OTP_STORAGE[mobile_number]
        return False
    
    return stored_otp == entered_otp

def normalize_mobile_number(mobile):
    """Normalize mobile number to a standard format for comparison"""
    if not mobile:
        return None
    
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, mobile))
    
    # Handle different formats
    if digits_only.startswith('91') and len(digits_only) == 12:
        # +91xxxxxxxxxx format
        return f"+91-{digits_only[2:]}"
    elif len(digits_only) == 10:
        # xxxxxxxxxx format (assume Indian number)
        return f"+91-{digits_only}"
    elif digits_only.startswith('0') and len(digits_only) == 11:
        # 0xxxxxxxxxx format
        return f"+91-{digits_only[1:]}"
    else:
        # Return as-is with +91- prefix if not already present
        if not mobile.startswith('+91'):
            return f"+91-{digits_only}"
        return mobile

def get_user_by_mobile(mobile_number):
    """Find user by mobile number (strict matching)"""
    normalized_input = normalize_mobile_number(mobile_number)
    
    for username, user_data in USERS_DB.items():
        stored_mobile = normalize_mobile_number(user_data['mobile'])
        if stored_mobile == normalized_input:
            return username, user_data
    
    return None, None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    full_name = request.form.get('full_name')
    username = request.form.get('username')
    email = request.form.get('email')
    mobile = request.form.get('mobile')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    # Validation
    if not all([full_name, username, email, mobile, password, confirm_password]):
        flash('All fields are required.', 'danger')
        return render_template('register.html')
    
    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return render_template('register.html')
    
    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return render_template('register.html')
    
    # Check if username already exists
    if username in USERS_DB:
        flash('Username already exists. Please choose a different one.', 'danger')
        return render_template('register.html')
    
    # Check if mobile number already exists
    normalized_mobile = normalize_mobile_number(mobile)
    for existing_user, user_data in USERS_DB.items():
        if normalize_mobile_number(user_data['mobile']) == normalized_mobile:
            flash('Mobile number already registered. Please use a different number.', 'danger')
            return render_template('register.html')
    
    # Create new user
    USERS_DB[username] = {
        'password': password,
        'mobile': normalized_mobile,
        'email': email,
        'full_name': full_name,
        'user_type': 'registered'
    }
    
    flash(f'Account created successfully for {full_name}! You can now login.', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check for any registered user credentials
    if username in USERS_DB and USERS_DB[username]['password'] == password:
        user_data = USERS_DB[username]
        session['logged_in'] = True
        session['username'] = username
        session['user_type'] = user_data['user_type']
        session['full_name'] = user_data['full_name']
        
        if user_data['user_type'] == 'primary':
            flash(f'Welcome back, {user_data["full_name"]}! You have full access to all features.', 'success')
        else:
            flash(f'Welcome, {user_data["full_name"]}! You are logged in successfully.', 'success')
        
        return redirect(url_for('home'))
    
    # Mock authentication - accept any non-empty credentials for demo
    elif username and password:
        session['logged_in'] = True
        session['username'] = username
        session['user_type'] = 'demo'
        session['full_name'] = username.title()
        flash('Demo access granted. For full features, use registered credentials.', 'info')
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    mobile_number = request.form.get('mobile_number')
    
    if not mobile_number:
        flash('Please enter a valid mobile number.', 'danger')
        return redirect(url_for('forgot_password'))
    
    # Normalize the mobile number
    normalized_mobile = normalize_mobile_number(mobile_number)
    
    # Find user by mobile number - strict validation
    username, user_data = None, None
    for user, data in USERS_DB.items():
        if normalize_mobile_number(data['mobile']) == normalized_mobile:
            username, user_data = user, data
            break
    
    if not user_data:
        flash('Mobile number not found in our records. Please use your registered mobile number.', 'danger')
        return redirect(url_for('forgot_password'))
    
    # Generate and store OTP
    otp = generate_otp()
    OTP_STORAGE[mobile_number] = {
        'otp': otp,
        'timestamp': datetime.now(),
        'username': username
    }
    
    # Send OTP (simulated)
    if send_otp_sms(mobile_number, otp):
        session['reset_mobile'] = mobile_number
        flash(f'OTP sent to {mobile_number}. Check console for demo OTP.', 'success')
        return redirect(url_for('verify_otp'))
    else:
        flash('Failed to send OTP. Please try again.', 'danger')
        return redirect(url_for('forgot_password'))

@app.route('/verify-otp')
def verify_otp():
    if 'reset_mobile' not in session:
        flash('Please start the password reset process again.', 'warning')
        return redirect(url_for('forgot_password'))
    return render_template('verify_otp.html', mobile=session['reset_mobile'])

@app.route('/verify-otp', methods=['POST'])
def verify_otp_post():
    if 'reset_mobile' not in session:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('forgot_password'))
    
    mobile_number = session['reset_mobile']
    entered_otp = request.form.get('otp')
    
    if is_otp_valid(mobile_number, entered_otp):
        # OTP is valid, allow password reset
        username = OTP_STORAGE[mobile_number]['username']
        session['reset_username'] = username
        # Clean up OTP
        del OTP_STORAGE[mobile_number]
        flash('OTP verified successfully! You can now reset your password.', 'success')
        return redirect(url_for('reset_password'))
    else:
        flash('Invalid or expired OTP. Please try again.', 'danger')
        return render_template('verify_otp.html', mobile=mobile_number)

@app.route('/reset-password')
def reset_password():
    if 'reset_username' not in session:
        flash('Please complete OTP verification first.', 'warning')
        return redirect(url_for('forgot_password'))
    return render_template('reset_password.html')

@app.route('/reset-password', methods=['POST'])
def reset_password_post():
    if 'reset_username' not in session:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('forgot_password'))
    
    username = session['reset_username']
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return render_template('reset_password.html')
    
    if new_password != confirm_password:
        flash('Passwords do not match. Please try again.', 'danger')
        return render_template('reset_password.html')
    
    # Update password in database
    USERS_DB[username]['password'] = new_password
    
    # Clean up session
    session.pop('reset_mobile', None)
    session.pop('reset_username', None)
    
    flash('Password reset successfully! You can now login with your new password.', 'success')
    return redirect(url_for('index'))

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'reset_mobile' not in session:
        return jsonify({'success': False, 'message': 'Session expired'})
    
    mobile_number = session['reset_mobile']
    username, user_data = get_user_by_mobile(mobile_number)
    
    if not user_data:
        return jsonify({'success': False, 'message': 'Mobile number not registered'})
    
    # Generate new OTP
    otp = generate_otp()
    OTP_STORAGE[mobile_number] = {
        'otp': otp,
        'timestamp': datetime.now(),
        'username': username
    }
    
    # Send OTP
    if send_otp_sms(mobile_number, otp):
        return jsonify({'success': True, 'message': 'OTP resent successfully'})
    
    return jsonify({'success': False, 'message': 'Failed to resend OTP'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('home.html', username=session.get('username'))

@app.route('/prediction')
def prediction():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('prediction.html')

@app.route('/performance')
def performance():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    metrics = predictor.get_model_performance()
    return render_template('performance.html', metrics=metrics)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/predict', methods=['POST'])
def predict():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Make prediction
            result = predictor.predict(filepath)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify(result)
            
        except Exception as e:
            # Clean up uploaded file on error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, or JPEG files.'}), 400

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)