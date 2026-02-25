from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Loan, Profile

loans = Blueprint('loans', __name__)

def get_current_profile():
    return Profile.query.filter_by(is_active=True).first()

@loans.route('/')
def index():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))
    user_loans = Loan.query.filter_by(profile_id=profile.id).all()
    return render_template('loans/index.html', loans=user_loans)

@loans.route('/add', methods=['GET', 'POST'])
def add():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        loan_type = request.form.get('type') # Given, Taken
        amount = float(request.form.get('amount'))
        interest = float(request.form.get('interest', 0))
        
        loan = Loan(
            profile_id=profile.id,
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
def edit(id):
    profile = get_current_profile()
    loan = Loan.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    
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
def delete(id):
    profile = get_current_profile()
    loan = Loan.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    
    db.session.delete(loan)
    db.session.commit()
    flash('Loan deleted.', 'info')
    return redirect(url_for('loans.index'))
