from datetime import datetime, UTC
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Transaction, Account, Category, Profile

transactions = Blueprint('transactions', __name__)

def get_current_profile():
    return Profile.query.filter_by(is_active=True).first()

@transactions.route('/')
def index():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))
    # Filter by profile via Account
    user_transactions = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Account.profile_id == profile.id).order_by(Transaction.date.desc()).all()
    return render_template('transactions/index.html', transactions=user_transactions)

@transactions.route('/add', methods=['GET', 'POST'])
def add():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))

    if request.method == 'POST':
        account_id = request.form.get('account_id')
        category_id = request.form.get('category_id')
        amount = float(request.form.get('amount'))
        transaction_type = request.form.get('type') # Income, Expense
        description = request.form.get('description')
        date_str = request.form.get('date')
        transaction_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now(UTC)
        
        # Security: Ensure account belongs to profile
        account = Account.query.filter_by(id=account_id, profile_id=profile.id).first_or_404()
        
        if transaction_type == 'Expense':
            account.balance -= amount
        else:
            account.balance += amount
            
        transaction = Transaction(
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            date=transaction_date
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction recorded!', 'success')
        return redirect(url_for('transactions.index'))
        
    accounts = Account.query.filter_by(profile_id=profile.id).all()
    categories = Category.query.all()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('transactions/add.html', accounts=accounts, categories=categories, today=today)

@transactions.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    profile = get_current_profile()
    transaction = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Transaction.id == id, Account.profile_id == profile.id).first_or_404()
    
    if request.method == 'POST':
        old_amount = transaction.amount
        old_type = transaction.transaction_type
        old_account = transaction.account
        
        # Reverse old balance change
        if old_type == 'Expense':
            old_account.balance += old_amount
        else:
            old_account.balance -= old_amount
            
        # Update transaction details
        new_account_id = request.form.get('account_id')
        # Security: Ensure new account belongs to profile
        new_account = Account.query.filter_by(id=new_account_id, profile_id=profile.id).first_or_404()
        
        transaction.account_id = new_account_id
        transaction.category_id = request.form.get('category_id')
        transaction.amount = float(request.form.get('amount'))
        transaction.transaction_type = request.form.get('type')
        transaction.description = request.form.get('description')
        date_str = request.form.get('date')
        if date_str:
            transaction.date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Apply new balance change
        if transaction.transaction_type == 'Expense':
            new_account.balance -= transaction.amount
        else:
            new_account.balance += transaction.amount
            
        db.session.commit()
        flash('Transaction updated!', 'success')
        return redirect(url_for('transactions.index'))
    
    accounts = Account.query.filter_by(profile_id=profile.id).all()
    categories = Category.query.all()
    return render_template('transactions/edit.html', transaction=transaction, accounts=accounts, categories=categories)

@transactions.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    profile = get_current_profile()
    transaction = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Transaction.id == id, Account.profile_id == profile.id).first_or_404()
    
    # Reverse the balance change before deleting
    account = transaction.account
    if transaction.transaction_type == 'Expense':
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount
        
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted.', 'info')
    return redirect(url_for('transactions.index'))
