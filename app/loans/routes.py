from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Loan

loans = Blueprint('loans', __name__)

@loans.route('/')
@login_required
def index():
    user_loans = Loan.query.filter_by(user_id=current_user.id).all()
    return render_template('loans/index.html', loans=user_loans)

@loans.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        loan_type = request.form.get('type') # Given, Taken
        amount = float(request.form.get('amount'))
        interest = float(request.form.get('interest', 0))
        
        loan = Loan(
            user=current_user,
            lender_borrower_name=name,
            loan_type=loan_type,
            total_amount=amount,
            remaining_balance=amount,
            interest_rate=interest,
            status='Active'
        )
        db.session.add(loan)
        db.session.commit()
        flash('Loan tracked!', 'success')
        return redirect(url_for('loans.index'))
        
    return render_template('loans/add.html')

@loans.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    loan = Loan.query.get_or_404(id)
    if loan.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('loans.index'))
    
    if request.method == 'POST':
        loan.lender_borrower_name = request.form.get('name')
        loan.loan_type = request.form.get('type')
        loan.total_amount = float(request.form.get('amount'))
        loan.interest_rate = float(request.form.get('interest_rate', 0))
        loan.status = request.form.get('status', 'Active')
        
        db.session.commit()
        flash('Loan updated!', 'success')
        return redirect(url_for('loans.index'))
    
    return render_template('loans/edit.html', loan=loan)

@loans.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    loan = Loan.query.get_or_404(id)
    if loan.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('loans.index'))
    
    db.session.delete(loan)
    db.session.commit()
    flash('Loan deleted.', 'info')
    return redirect(url_for('loans.index'))
