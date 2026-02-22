from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Account, Currency
from seed_data import seed_currencies

accounts = Blueprint('accounts', __name__)

@accounts.route('/')
@login_required
def index():
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('accounts/index.html', accounts=user_accounts)

@accounts.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        account_type = request.form.get('account_type')
        balance = float(request.form.get('balance', 0))
        color = request.form.get('color', '#4f46e5')
        currency_id = request.form.get('currency_id')
        
        if not currency_id:
            bdt = Currency.query.filter_by(code='BDT').first()
            currency_id = bdt.id if bdt else None
        
        new_account = Account(
            user_id=current_user.id,
            name=name,
            account_type=account_type,
            balance=balance,
            color_theme=color,
            currency_id=currency_id
        )
        db.session.add(new_account)
        db.session.commit()
        flash('Account added successfully!', 'success')
        return redirect(url_for('accounts.index'))
    
    seed_currencies()
    currencies = Currency.query.all()
    return render_template('accounts/add.html', currencies=currencies)

@accounts.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    account = Account.query.get_or_404(id)
    if account.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('accounts.index'))
    
    if request.method == 'POST':
        account.name = request.form.get('name')
        account.account_type = request.form.get('account_type')
        account.balance = float(request.form.get('balance', 0))
        account.color_theme = request.form.get('color', '#4f46e5')
        account.currency_id = request.form.get('currency_id')
        
        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('accounts.index'))
    
    seed_currencies()
    currencies = Currency.query.all()
    return render_template('accounts/edit.html', account=account, currencies=currencies)

@accounts.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    account = Account.query.get_or_404(id)
    if account.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('accounts.index'))
    
    db.session.delete(account)
    db.session.commit()
    flash('Account deleted.', 'info')
    return redirect(url_for('accounts.index'))
