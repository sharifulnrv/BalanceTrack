from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Profile

profiles = Blueprint('profiles', __name__)

@profiles.route('/')
def index():
    all_profiles = Profile.query.all()
    return render_template('profiles/index.html', profiles=all_profiles)

@profiles.route('/add', methods=['POST'])
def add():
    name = request.form.get('name')
    if name:
        if Profile.query.filter_by(name=name).first():
            flash('Profile already exists!', 'danger')
        else:
            # If this is the first profile, make it active
            is_active = Profile.query.count() == 0
            new_profile = Profile(name=name, is_active=is_active)
            db.session.add(new_profile)
            db.session.commit()
            flash(f'Profile "{name}" created successfully!', 'success')
    return redirect(url_for('profiles.index'))

@profiles.route('/switch/<int:id>')
def switch(id):
    Profile.query.update({Profile.is_active: False})
    profile = Profile.query.get_or_404(id)
    profile.is_active = True
    db.session.commit()
    flash(f'Switched to profile: {profile.name}', 'success')
    return redirect(url_for('main.index'))
