# main/routes.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('auth.chat_dashboard'))  # 👈 Redirect logged-in users
    return render_template('index.html')  # 👈 Show landing to others

@main.route('/terms')
def terms():
    return render_template('terms.html')

@main.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')
