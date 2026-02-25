from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Category, Profile

categories = Blueprint('categories', __name__)

def get_current_profile():
    return Profile.query.filter_by(is_active=True).first()

@categories.route('/')
def index():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))
    # Show categories from this profile or global ones (profile_id is NULL)
    user_categories = Category.query.filter((Category.profile_id == profile.id) | (Category.profile_id == None)).all()
    return render_template('categories/index.html', categories=user_categories)

@categories.route('/add', methods=['GET', 'POST'])
def add():
    profile = get_current_profile()
    if not profile:
        return redirect(url_for('profiles.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon', 'ph-tag')
        color = request.form.get('color', '#4f46e5')
        is_income = request.form.get('type') == 'Income'
        
        new_category = Category(
            profile_id=profile.id,
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
def edit(id):
    profile = get_current_profile()
    category = Category.query.filter((Category.id == id) & ((Category.profile_id == profile.id) | (Category.profile_id == None))).first_or_404()
    
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
def delete(id):
    profile = get_current_profile()
    category = Category.query.filter_by(id=id, profile_id=profile.id).first_or_404()
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('categories.index'))
