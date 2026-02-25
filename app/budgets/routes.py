from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Budget, Category, Profile

budgets = Blueprint('budgets', __name__)

def get_current_profile():
    return Profile.query.filter_by(is_active=True).first()

@budgets.route('/')
def index():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))
    user_budgets = Budget.query.filter_by(profile_id=profile.id).all()
    return render_template('budgets/index.html', budgets=user_budgets)

@budgets.route('/add', methods=['GET', 'POST'])
def add():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))

    if request.method == 'POST':
        category_id = request.form.get('category_id')
        amount = float(request.form.get('amount'))
        period = request.form.get('period') # Monthly, Yearly
        
        budget = Budget(
            profile_id=profile.id,
            category_id=category_id,
            amount=amount,
            period=period
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget set!', 'success')
        return redirect(url_for('budgets.index'))
        
    # Show categories from this profile or global ones
    categories = Category.query.filter((Category.profile_id == profile.id) | (Category.profile_id == None)).all()
    return render_template('budgets/add.html', categories=categories)

@budgets.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    profile = get_current_profile()
    budget = Budget.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    
    if request.method == 'POST':
        budget.category_id = request.form.get('category_id')
        budget.amount = float(request.form.get('amount'))
        budget.period = request.form.get('period')
        
        db.session.commit()
        flash('Budget updated!', 'success')
        return redirect(url_for('budgets.index'))
    
    categories = Category.query.filter((Category.profile_id == profile.id) | (Category.profile_id == None)).all()
    return render_template('budgets/edit.html', budget=budget, categories=categories)

@budgets.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    profile = get_current_profile()
    budget = Budget.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    
    db.session.delete(budget)
    db.session.commit()
    flash('Budget removed.', 'info')
    return redirect(url_for('budgets.index'))
