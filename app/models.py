from datetime import datetime, UTC
from hashlib import sha256
from app import db, login_manager
from flask_login import UserMixin
import bcrypt
import uuid

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    telegram_chat_id = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_verified = db.Column(db.Boolean, default=False)
    base_currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    base_currency = db.relationship('Currency', foreign_keys=[base_currency_id])
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    accounts = db.relationship('Account', backref='owner', lazy='dynamic')
    categories = db.relationship('Category', backref='owner', lazy='dynamic')
    loans = db.relationship('Loan', backref='user', lazy='dynamic')
    investments = db.relationship('Investment', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class OTPLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp_hash = db.Column(db.String(128), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    retry_count = db.Column(db.Integer, default=0)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False) # USD, BDT, etc.
    symbol = db.Column(db.String(5))
    exchange_rate = db.Column(db.Float, default=1.0) # Relative to base currency
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    account_type = db.Column(db.String(32)) # Bank, Cash, Credit Card, etc.
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    currency = db.relationship('Currency', backref='accounts')
    balance = db.Column(db.Float, default=0.0)
    color_theme = db.Column(db.String(20))
    icon = db.Column(db.String(64))
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    transactions = db.relationship(
        'Transaction', 
        foreign_keys='Transaction.account_id',
        backref='account', 
        lazy='dynamic', 
        cascade="all, delete-orphan"
    )
    
    transfers_in = db.relationship(
        'Transaction',
        foreign_keys='Transaction.transfer_to_account_id',
        backref='transfer_destination',
        lazy='dynamic'
    )

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id')) # For subcategories
    icon = db.Column(db.String(64))
    color = db.Column(db.String(20))
    is_income = db.Column(db.Boolean, default=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='transactions')
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20)) # Income, Expense, Transfer
    description = db.Column(db.String(256))
    tags = db.Column(db.String(128))
    date = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    attachment_path = db.Column(db.String(256))
    is_recurring = db.Column(db.Boolean, default=False)
    transfer_to_account_id = db.Column(db.Integer, db.ForeignKey('account.id')) # For Transfers
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20)) # Monthly, Yearly
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lender_borrower_name = db.Column(db.String(128), nullable=False)
    loan_type = db.Column(db.String(20)) # Given, Taken
    total_amount = db.Column(db.Float, nullable=False)
    remaining_balance = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20)) # Active, Paid

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    asset_type = db.Column(db.String(32)) # Stock, Crypto, FD, etc.
    principal_amount = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(256))
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
