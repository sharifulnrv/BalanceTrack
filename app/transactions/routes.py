from datetime import datetime, UTC
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, Account, Category

transactions = Blueprint('transactions', __name__)

@transactions.route('/')
@login_required
def index():
    user_transactions = Transaction.query.join(Account, Transaction.account_id == Account.id).filter(Account.user_id == current_user.id).order_by(Transaction.date.desc()).all()
    return render_template('transactions/index.html', transactions=user_transactions)

@transactions.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        category_id = request.form.get('category_id')
        amount = float(request.form.get('amount'))
        transaction_type = request.form.get('type') # Income, Expense
        description = request.form.get('description')
        date_str = request.form.get('date')
        transaction_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now(UTC)
        
        account = Account.query.get(account_id)
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
        
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('transactions/add.html', accounts=user_accounts, categories=categories, today=today)

@transactions.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.account.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('transactions.index'))
    
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
        transaction.account_id = request.form.get('account_id')
        transaction.category_id = request.form.get('category_id')
        transaction.amount = float(request.form.get('amount'))
        transaction.transaction_type = request.form.get('type')
        transaction.description = request.form.get('description')
        date_str = request.form.get('date')
        if date_str:
            transaction.date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Apply new balance change
        new_account = Account.query.get(transaction.account_id)
        if transaction.transaction_type == 'Expense':
            new_account.balance -= transaction.amount
        else:
            new_account.balance += transaction.amount
            
        db.session.commit()
        flash('Transaction updated!', 'success')
        return redirect(url_for('transactions.index'))
    
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('transactions/edit.html', transaction=transaction, accounts=user_accounts, categories=categories)

@transactions.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.account.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('transactions.index'))
    
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
