"""
Flask Login Authentication System
Features: Registration, Login, Password Reset, Email, SQLite Database, Session Management
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from functools import wraps
import os
import secrets
from datetime import datetime, timedelta, timezone
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration - Update these for production
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@securelogin.com')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)


# ==================== MODELS ====================

class User(db.Model):
    """User model with authentication fields."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    login_history = db.relationship('LoginHistory', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set user password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verify password against hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        """Generate password reset token."""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token):
        """Verify if reset token is valid."""
        if self.reset_token != token:
            return False
        if self.reset_token_expiry is None or datetime.now(timezone.utc) > self.reset_token_expiry:
            return False
        return True

    def clear_reset_token(self):
        """Clear reset token after use."""
        self.reset_token = None
        self.reset_token_expiry = None

    def __repr__(self):
        return f'<User {self.username}>'


class LoginHistory(db.Model):
    """Login attempt history model."""
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, default=True)

    def __repr__(self):
        status = "Success" if self.success else "Failed"
        return f'<LoginHistory {self.user.username} - {status}>'


# ==================== VALIDATORS ====================

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),\.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is valid."


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# ==================== DECORATORS ====================

def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_client_ip():
    """Get client IP address."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        # Validation
        if not all([username, email, password, confirm]):
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if not validate_email(email):
            flash('Invalid email format.', 'error')
            return render_template('register.html')

        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'error')
            return render_template('register.html')

        # Check existing user
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not all([username, password]):
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('User not found.', 'error')
            return render_template('login.html')

        if not user.is_active:
            flash('Account is deactivated.', 'error')
            return render_template('login.html')

        if user.check_password(password):
            # Successful login
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True

            user.last_login = datetime.now(timezone.utc)

            # Log successful attempt
            history = LoginHistory(
                user_id=user.id,
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                success=True
            )
            db.session.add(history)
            db.session.commit()

            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Log failed attempt
            history = LoginHistory(
                user_id=user.id,
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                success=False
            )
            db.session.add(history)
            db.session.commit()

            flash('Invalid password.', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout route."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route."""
    user = db.session.get(User, session['user_id'])
    if user is None:
        session.clear()
        return redirect(url_for('login'))
    history = LoginHistory.query.filter_by(user_id=user.id).order_by(
        LoginHistory.login_time.desc()).limit(10).all()
    return render_template('dashboard.html', user=user, history=history)


# ==================== PASSWORD RESET ====================

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email.', 'error')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if not user:
            # Don't reveal if email exists
            flash('If this email exists, reset instructions have been sent.', 'success')
            return render_template('forgot_password.html')

        # Generate token
        token = user.generate_reset_token()
        db.session.commit()

        # Send email
        reset_url = url_for('reset_password', token=token, _external=True)

        try:
            msg = Message(
                'Password Reset Request',
                recipients=[user.email],
                html=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #e94560;">Password Reset Request</h2>
                    <p>Hi {user.username},</p>
                    <p>You requested a password reset for your Secure Login System account.</p>
                    <p>Click the link below to reset your password (expires in 1 hour):</p>
                    <a href="{reset_url}" style="display: inline-block; padding: 12px 24px; 
                       background: #e94560; color: white; text-decoration: none; 
                       border-radius: 8px; margin: 16px 0;">Reset Password</a>
                    <p>Or copy this URL: {reset_url}</p>
                    <p style="color: #666; font-size: 13px;">If you didn't request this, ignore this email.</p>
                </div>
                """
            )
            mail.send(msg)
            flash('Password reset instructions have been sent to your email.', 'success')
        except Exception as e:
            app.logger.error(f'Failed to send email: {e}')
            # For development, show token
            flash(f'Email service unavailable. Your reset token: {token}', 'warning')

        return render_template('forgot_password.html')

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)

        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'error')
            return render_template('reset_password.html', token=token)

        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()

        flash('Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    flash('Page not found.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def server_error(e):
    flash('An error occurred. Please try again.', 'error')
    return redirect(url_for('index'))


# ==================== CLI COMMANDS ====================

@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized successfully!')


@app.cli.command('create-admin')
def create_admin():
    """Create admin user."""
    import click
    username = click.prompt('Username')
    email = click.prompt('Email')
    password = click.prompt('Password', hide_input=True)

    if User.query.filter_by(username=username).first():
        print('Username already exists.')
        return

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f'Admin user {username} created successfully!')


# ==================== MAIN ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
