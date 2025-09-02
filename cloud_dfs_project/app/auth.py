from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
import re

auth = Blueprint('auth', __name__)

def is_valid_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Password validation - at least 6 characters"""
    return len(password) >= 6

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if user.is_active:
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('main.index'))
            else:
                flash('Your account has been deactivated.', 'error')
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or not is_valid_email(email):
            errors.append('Please enter a valid email address.')
        
        if not password or not is_valid_password(password):
            errors.append('Password must be at least 6 characters long.')
        
        if password != password_confirm:
            errors.append('Passwords do not match.')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    new_password_confirm = request.form.get('new_password_confirm', '')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.profile'))
    
    if not is_valid_password(new_password):
        flash('New password must be at least 6 characters long.', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != new_password_confirm:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to change password. Please try again.', 'error')
        print(f"Password change error: {e}")
    
    return redirect(url_for('auth.profile'))

# API Routes for authentication
@auth.route('/api/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if user and user.check_password(password) and user.is_active:
        login_user(user)
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@auth.route('/api/register', methods=['POST'])
def api_register():
    """API registration endpoint"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Validation
    if not username or len(username) < 3:
        return jsonify({'success': False, 'message': 'Username must be at least 3 characters'}), 400
    
    if not email or not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Invalid email address'}), 400
    
    if not password or not is_valid_password(password):
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    # Check existing users
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    try:
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Registration failed'}), 500

@auth.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """API logout endpoint"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logout successful'})

@auth.route('/api/profile', methods=['GET'])
@login_required
def api_profile():
    """API profile endpoint"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })
