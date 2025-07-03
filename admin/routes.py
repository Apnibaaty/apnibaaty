# admin/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Character, Message

admin = Blueprint('admin', __name__, url_prefix='/admin')

# Simple admin check (you can expand this later)
def is_admin():
    return current_user.is_authenticated and current_user.email == "apnibaaty@gmail.com"

@admin.route('/dashboard')  # ✅ FIXED
@login_required
def dashboard():
    if not is_admin():
        flash("Access denied. Admins only.")
        return redirect(url_for('chat_dashboard'))

    total_users = User.query.count()
    total_messages = Message.query.count()
    total_characters = Character.query.count()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_messages=total_messages,
                           total_characters=total_characters)

@admin.route('/users')
@login_required
def list_users():
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('admin.list_users'))

    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin.route('/user/<int:user_id>')
@login_required
def user_detail(user_id):
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('chat_dashboard'))

    user = User.query.get_or_404(user_id)
    messages = Message.query.filter_by(user_id=user.id).all()
    return render_template('admin/user_detail.html', user=user, messages=messages)


@admin.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('chat_dashboard'))

    user = User.query.get_or_404(user_id)
    Message.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for('admin.list_users'))

@admin.route('/user/<int:user_id>/delete-chats', methods=['POST'])
@login_required
def delete_user_chats(user_id):
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('auth.login'))

    Message.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    flash("All chat messages for this user have been deleted.")
    return redirect(url_for('admin.edit_user', user_id=user_id))


@admin.route('/characters')
@login_required
def manage_characters():
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('chat_dashboard'))

    characters = Character.query.all()
    return render_template('admin/manage_characters.html', characters=characters)

@admin.route('/delete-character/<int:char_id>', methods=['POST'])
@login_required
def delete_character(char_id):
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('chat_dashboard'))

    char = Character.query.get_or_404(char_id)
    db.session.delete(char)
    db.session.commit()
    flash("Character deleted.")
    return redirect(url_for('admin.manage_characters'))

@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('chat_dashboard'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.age = request.form.get('age') or None
        user.gender = request.form['gender']
        user.ai_preference = request.form['ai_preference']
        user.remaining_messages = int(request.form['remaining_messages'])
        user.ads_watched = int(request.form['ads_watched'])
        db.session.commit()
        flash("User updated successfully.")
        return redirect(url_for('admin.user_detail', user_id=user.id))

    return render_template('admin/edit_user.html', user=user)

@admin.route('/character/<int:char_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_character(char_id):
    if not is_admin():
        flash("Access denied")
        return redirect(url_for('chat_dashboard'))

    char = Character.query.get_or_404(char_id)

    if request.method == 'POST':
        char.name = request.form['name']
        char.gender = request.form['gender']
        char.tags = request.form['tags']
        char.description = request.form['description']
        char.appearance = request.form['appearance_description']
        db.session.commit()
        flash("Character updated successfully.")
        return redirect(url_for('admin.manage_characters'))

    return render_template('admin/edit_character.html', character=char)

@admin.route('/user/<int:user_id>/chat')
@login_required
def view_user_chat(user_id):
    if not is_admin():
        flash("Access denied.")
        return redirect(url_for('chat_dashboard'))

    user = User.query.get_or_404(user_id)
    messages = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp.asc()).all()

    return render_template('admin/user_chat.html', user=user, messages=messages)
