from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Category

categories = Blueprint('categories', __name__)

@categories.route('/')
@login_required
def index():
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories/index.html', categories=user_categories)

@categories.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon', 'ph-tag')
        color = request.form.get('color', '#4f46e5')
        is_income = request.form.get('type') == 'Income'
        
        new_category = Category(
            user_id=current_user.id,
            name=name,
            icon=icon,
            color=color,
            is_income=is_income
        )
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        
        # Check if we should redirect back to a previous page (like Add Transaction)
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
            
        return redirect(url_for('categories.index'))
    
    return render_template('categories/add.html')

@categories.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.get_or_404(id)
    if category.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('categories.index'))
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.icon = request.form.get('icon')
        category.color = request.form.get('color')
        category.is_income = request.form.get('type') == 'Income'
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('categories.index'))
    
    return render_template('categories/edit.html', category=category)

@categories.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.get_or_404(id)
    if category.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('categories.index'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('categories.index'))
