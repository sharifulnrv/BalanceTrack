from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, ActivityLog
from app.auth.otp_service import OTPService
from seed_data import seed_categories, seed_currencies

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_verified:
                session['pending_user_id'] = user.id
                OTPService.create_otp_for_user(user)
                flash('Please verify your account with the OTP sent to your Telegram.', 'info')
                return redirect(url_for('auth.verify_otp'))
            
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
            
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        telegram_chat_id = request.form.get('telegram_chat_id')
        password = request.form.get('password')
        
        user_exists = User.query.filter((User.username == username) | (User.telegram_chat_id == telegram_chat_id)).first()
        if user_exists:
            flash('Username or Telegram Chat ID already registered.', 'warning')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, telegram_chat_id=telegram_chat_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session['pending_user_id'] = user.id
        if OTPService.create_otp_for_user(user):
            flash('Registration successful! OTP sent to your Telegram.', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Error sending OTP. Please check your Telegram Chat ID and bot status.', 'danger')
            
    return render_template('auth/register.html')

@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('pending_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        otp = request.form.get('otp')
        success, message = OTPService.verify_otp(user_id, otp)
        
        if success:
            user.is_verified = True
            db.session.commit()
            
            # Seed default categories and currencies
            seed_currencies()
            seed_categories(user.id)
            
            login_user(user)
            session.pop('pending_user_id', None)
            flash('Account verified and logged in!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash(message, 'danger')
            
    return render_template('auth/verify_otp.html')

@auth.route('/resend-otp')
def resend_otp():
    user_id = session.get('pending_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if OTPService.create_otp_for_user(user):
        flash('A new OTP has been sent to your Telegram.', 'info')
    else:
        flash('Failed to resend OTP.', 'danger')
        
    return redirect(url_for('auth.verify_otp'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        telegram_chat_id = request.form.get('telegram_chat_id')
        user = User.query.filter_by(telegram_chat_id=telegram_chat_id).first()
        
        if user:
            session['reset_user_id'] = user.id
            if OTPService.create_otp_for_user(user):
                flash('OTP sent to your Telegram for password reset.', 'info')
                return redirect(url_for('auth.verify_reset_otp'))
            else:
                flash('Error sending OTP. Please check your Telegram.', 'danger')
        else:
            flash('No account found with that Telegram Chat ID.', 'warning')
            
    return render_template('auth/forgot_password.html')

@auth.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    user_id = session.get('reset_user_id')
    if not user_id:
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        success, message = OTPService.verify_otp(user_id, otp)
        
        if success:
            flash('Identity verified. Please set a new password.', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash(message, 'danger')
            
    return render_template('auth/verify_reset_otp.html')

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    user_id = session.get('reset_user_id')
    if not user_id:
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.reset_password'))
        
        user = User.query.get(user_id)
        user.set_password(password)
        db.session.commit()
        
        session.pop('reset_user_id', None)
        flash('Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
