from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Budget, Category

budgets = Blueprint('budgets', __name__)

@budgets.route('/')
@login_required
def index():
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets/index.html', budgets=user_budgets)

@budgets.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        amount = float(request.form.get('amount'))
        period = request.form.get('period') # Monthly, Yearly
        
        budget = Budget(
            user=current_user,
            category_id=category_id,
            amount=amount,
            period=period
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget set!', 'success')
        return redirect(url_for('budgets.index'))
        
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets/add.html', categories=categories)

@budgets.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('budgets.index'))
    
    if request.method == 'POST':
        budget.category_id = request.form.get('category_id')
        budget.amount = float(request.form.get('amount'))
        budget.period = request.form.get('period')
        
        db.session.commit()
        flash('Budget updated!', 'success')
        return redirect(url_for('budgets.index'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets/edit.html', budget=budget, categories=categories)

@budgets.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('budgets.index'))
    
    db.session.delete(budget)
    db.session.commit()
    flash('Budget removed.', 'info')
    return redirect(url_for('budgets.index'))
