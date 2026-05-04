"""
Database models and configuration for Flask-SQLAlchemy
Provides persistent user authentication using SQLite
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    """
    User model for authentication
    
    Attributes:
        id: Primary key
        username: Unique username
        email: User email address
        password_hash: Hashed password (never store plain text!)
        full_name: User's full name
        mobile: Mobile phone number
        user_type: Type of user (primary, registered, demo)
        created_at: Account creation timestamp
        last_login: Last login timestamp
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_type = db.Column(db.String(20), default='registered')  # primary, registered, demo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        Hash and set user password
        
        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify password against stored hash
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches
        """
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """
        Convert user object to dictionary
        
        Returns:
            dict: User data (excluding password hash)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'mobile': self.mobile,
            'user_type': self.user_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class OTP(db.Model):
    """
    OTP (One-Time Password) model for password reset
    
    Attributes:
        id: Primary key
        mobile: Mobile number
        otp_code: 6-digit OTP code
        username: Associated username
        created_at: OTP generation timestamp
        expires_at: OTP expiration timestamp
        is_used: Whether OTP has been used
    """
    
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(20), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<OTP {self.mobile}>'
    
    def is_valid(self):
        """
        Check if OTP is still valid
        
        Returns:
            bool: True if OTP is not expired and not used
        """
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        db.session.commit()

def init_db(app):
    """
    Initialize database with Flask app
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default primary user if not exists
        primary_user = User.query.filter_by(username='rakshith').first()
        if not primary_user:
            primary_user = User(
                username='rakshith',
                email='rakshith@medicalai.com',
                full_name='Dr. Rakshith',
                mobile='+91-9390175239',
                user_type='primary'
            )
            primary_user.set_password('Rakshith@21')
            db.session.add(primary_user)
            db.session.commit()
            print("✓ Default primary user created: rakshith")
        else:
            print("✓ Primary user already exists")
        
        print(f"✓ Database initialized: {app.config['SQLALCHEMY_DATABASE_URI']}")

def normalize_mobile_number(mobile):
    """
    Normalize mobile number to standard format
    
    Args:
        mobile: Mobile number in any format
        
    Returns:
        str: Normalized mobile number (+91-XXXXXXXXXX)
    """
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
