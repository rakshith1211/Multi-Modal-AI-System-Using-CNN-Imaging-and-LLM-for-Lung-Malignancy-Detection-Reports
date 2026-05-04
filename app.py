from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
from werkzeug.utils import secure_filename
from predictor import LungCancerPredictor
import json
from dotenv import load_dotenv
import random
import time
from datetime import datetime, timedelta
from database import db, User, OTP, init_db, normalize_mobile_number

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # Set to True for SQL query logging

# Initialize database
init_db(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize predictor (will be cached after first load)
predictor = None

def get_predictor():
    """
    Get or initialize predictor (lazy loading with caching)
    This avoids loading the model on every request
    """
    global predictor
    if predictor is None:
        predictor = LungCancerPredictor()
    return predictor

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
    return True

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
    """Handle user registration with database storage"""
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
    
    # Normalize mobile number
    normalized_mobile = normalize_mobile_number(mobile)
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists. Please choose a different one.', 'danger')
        return render_template('register.html')
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        flash('Email already registered. Please use a different email.', 'danger')
        return render_template('register.html')
    
    # Check if mobile number already exists
    if User.query.filter_by(mobile=normalized_mobile).first():
        flash('Mobile number already registered. Please use a different number.', 'danger')
        return render_template('register.html')
    
    try:
        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            mobile=normalized_mobile,
            user_type='registered'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Account created successfully for {full_name}! You can now login.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Registration failed: {str(e)}', 'danger')
        return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle user login with database authentication"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please enter both username and password.', 'danger')
        return redirect(url_for('index'))
    
    # Query user from database
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        # Successful login
        session['logged_in'] = True
        session['username'] = user.username
        session['user_type'] = user.user_type
        session['full_name'] = user.full_name
        session['user_id'] = user.id
        
        # Update last login timestamp
        user.update_last_login()
        
        if user.user_type == 'primary':
            flash(f'Welcome back, {user.full_name}! You have full access to all features.', 'success')
        else:
            flash(f'Welcome, {user.full_name}! You are logged in successfully.', 'success')
        
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP for password reset"""
    mobile_number = request.form.get('mobile_number')
    
    if not mobile_number:
        flash('Please enter a valid mobile number.', 'danger')
        return redirect(url_for('forgot_password'))
    
    # Normalize the mobile number
    normalized_mobile = normalize_mobile_number(mobile_number)
    
    # Find user by mobile number
    user = User.query.filter_by(mobile=normalized_mobile).first()
    
    if not user:
        flash('Mobile number not found in our records. Please use your registered mobile number.', 'danger')
        return redirect(url_for('forgot_password'))
    
    # Generate OTP
    otp_code = generate_otp()
    
    # Store OTP in database
    # Delete any existing OTPs for this mobile
    OTP.query.filter_by(mobile=normalized_mobile, is_used=False).delete()
    
    new_otp = OTP(
        mobile=normalized_mobile,
        otp_code=otp_code,
        username=user.username,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.session.add(new_otp)
    db.session.commit()
    
    # Send OTP (simulated)
    if send_otp_sms(normalized_mobile, otp_code):
        session['reset_mobile'] = normalized_mobile
        flash(f'OTP sent to {normalized_mobile}. Check console for demo OTP.', 'success')
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
    """Verify OTP for password reset"""
    if 'reset_mobile' not in session:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('forgot_password'))
    
    mobile_number = session['reset_mobile']
    entered_otp = request.form.get('otp')
    
    # Find valid OTP in database
    otp_record = OTP.query.filter_by(
        mobile=mobile_number,
        otp_code=entered_otp,
        is_used=False
    ).first()
    
    if otp_record and otp_record.is_valid():
        # OTP is valid
        session['reset_username'] = otp_record.username
        otp_record.mark_as_used()
        
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
    """Reset user password"""
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
    user = User.query.filter_by(username=username).first()
    if user:
        user.set_password(new_password)
        db.session.commit()
        
        # Clean up session
        session.pop('reset_mobile', None)
        session.pop('reset_username', None)
        
        flash('Password reset successfully! You can now login with your new password.', 'success')
        return redirect(url_for('index'))
    else:
        flash('User not found. Please try again.', 'danger')
        return redirect(url_for('forgot_password'))

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP for password reset"""
    if 'reset_mobile' not in session:
        return jsonify({'success': False, 'message': 'Session expired'})
    
    mobile_number = session['reset_mobile']
    
    # Find user by mobile
    user = User.query.filter_by(mobile=mobile_number).first()
    
    if not user:
        return jsonify({'success': False, 'message': 'Mobile number not registered'})
    
    # Generate new OTP
    otp_code = generate_otp()
    
    # Delete old OTPs
    OTP.query.filter_by(mobile=mobile_number, is_used=False).delete()
    
    # Create new OTP
    new_otp = OTP(
        mobile=mobile_number,
        otp_code=otp_code,
        username=user.username,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.session.add(new_otp)
    db.session.commit()
    
    # Send OTP
    if send_otp_sms(mobile_number, otp_code):
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
    """Display model performance metrics"""
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    pred = get_predictor()
    metrics = pred.get_model_performance()
    return render_template('performance.html', metrics=metrics)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle image prediction requests"""
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
            # Make prediction using cached predictor
            pred = get_predictor()
            result = pred.predict(filepath)
            
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