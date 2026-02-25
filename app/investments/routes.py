from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Investment, Profile

investments = Blueprint('investments', __name__)

def get_current_profile():
    return Profile.query.filter_by(is_active=True).first()

@investments.route('/')
def index():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))
    user_investments = Investment.query.filter_by(profile_id=profile.id).all()
    return render_template('investments/index.html', investments=user_investments)

@investments.route('/add', methods=['GET', 'POST'])
def add():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        asset_type = request.form.get('type') # Stock, Crypto, FD
        principal = float(request.form.get('principal'))
        
        investment = Investment(
            profile_id=profile.id,
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
def edit(id):
    profile = get_current_profile()
    investment = Investment.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    
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
def delete(id):
    profile = get_current_profile()
    investment = Investment.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    
    db.session.delete(investment)
    db.session.commit()
    flash('Investment deleted.', 'info')
    return redirect(url_for('investments.index'))
