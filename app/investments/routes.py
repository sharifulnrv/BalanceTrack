from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Investment

investments = Blueprint('investments', __name__)

@investments.route('/')
@login_required
def index():
    user_investments = Investment.query.filter_by(user_id=current_user.id).all()
    return render_template('investments/index.html', investments=user_investments)

@investments.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        asset_type = request.form.get('type') # Stock, Crypto, FD
        principal = float(request.form.get('principal'))
        
        investment = Investment(
            user=current_user,
            name=name,
            asset_type=asset_type,
            principal_amount=principal,
            current_value=principal
        )
        db.session.add(investment)
        db.session.commit()
        flash('Investment tracked!', 'success')
        return redirect(url_for('investments.index'))
        
    return render_template('investments/add.html')

@investments.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    investment = Investment.query.get_or_404(id)
    if investment.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('investments.index'))
    
    if request.method == 'POST':
        investment.name = request.form.get('name')
        investment.asset_type = request.form.get('asset_type')
        investment.principal_amount = float(request.form.get('principal_amount'))
        investment.current_value = float(request.form.get('current_value'))
        
        db.session.commit()
        flash('Investment updated!', 'success')
        return redirect(url_for('investments.index'))
    
    return render_template('investments/edit.html', investment=investment)

@investments.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    investment = Investment.query.get_or_404(id)
    if investment.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('investments.index'))
    
    db.session.delete(investment)
    db.session.commit()
    flash('Investment deleted.', 'info')
    return redirect(url_for('investments.index'))
