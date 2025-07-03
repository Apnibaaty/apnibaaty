from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Message, Character
from openai import OpenAI
import traceback  # at the top of your file
import os
import re  # ✅ Add this at the top if not already imported

auth = Blueprint('auth', __name__)

# ✅ Load API Key (use environment variable or fallback to None)
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY != "your-openai-api-key" else None

# LOGIN (handles both admin and user)
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user:
            print("Stored password (hashed):", user.password)
            print("Entered password:", password)
            print("Password match:", check_password_hash(user.password, password))
            
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.email == 'apnibaaty@gmail.com':
                return redirect(url_for('admin.dashboard'))  # Admin
            return redirect(url_for('chat_dashboard'))  # Normal user

        flash("Invalid credentials")
        return redirect(url_for('auth.login'))

    return render_template('login.html')

# SIGNUP
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = request.form['age']

        # ✅ Email format validation using regex
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash("Invalid email format.")
            return redirect(url_for('auth.signup'))

        if int(age) < 18:
            flash("You must be 18+ to use this app.")
            return redirect(url_for('auth.signup'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists.")
            return redirect(url_for('auth.signup'))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            age=int(age),
            gender=None,
            ai_preference=None,
            remaining_messages=30,  # ✅ Give 30 messages at signup
            ads_watched=0
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('auth.complete_profile'))

    return render_template('signup.html')

# LOGOUT
@auth.route('/logout')
@login_required
def logout():
    # Delete user chat history on logout
    Message.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    logout_user()
    return redirect(url_for('main.home'))

# GOOGLE LOGIN (placeholder)
@auth.route('/google-login')
def google_login():
    return "Google login coming soon."

# COMPLETE PROFILE
@auth.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if request.method == 'POST':
        current_user.gender = request.form['gender']
        current_user.ai_preference = request.form['ai_preference']
        db.session.commit()
        return redirect(url_for('chat_dashboard'))

    return render_template('complete_profile.html')

# CHAT ROOM
@auth.route('/chat/<character>', methods=['GET'])
@login_required
def chat_room(character):
    messages = Message.query.filter_by(user_id=current_user.id, character=character).order_by(Message.id).all()
    return render_template('chat_room.html', character_name=character, character_img='default.jpg', messages=messages)

# SEND MESSAGE (AJAX)
@auth.route('/send_message/<character>', methods=['POST'])
@login_required
def send_message(character):
    # Ensure user has a valid remaining_messages value
    if current_user.remaining_messages is None:
        current_user.remaining_messages = 0

    # Block if no messages left
    if current_user.remaining_messages <= 0:
        return jsonify({"error": "You have used all your messages. Watch ads to unlock more."}), 403

    # Get message from user
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': 'Message is empty'}), 400

    # Save user's message
    user_msg = Message(
        user_id=current_user.id,
        character=character,
        sender='user',
        content=user_message
    )
    db.session.add(user_msg)

    # Use OpenAI if available, else use mock response
    try:
        if client:
            is_premium = getattr(current_user, 'is_premium', False)
            if is_premium:
                past_msgs = Message.query.filter_by(user_id=current_user.id, character=character).order_by(Message.id).all()
                context = [{'role': 'user' if m.sender == 'user' else 'assistant', 'content': m.content} for m in past_msgs]
            else:
                context = [{'role': 'user', 'content': user_message}]
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=context
            )
            ai_reply = response.choices[0].message.content.strip()
        else:
            raise Exception("OpenAI client not configured.")
    except Exception as e:
        ai_reply = f"This is a mock AI reply to: '{user_message}' 🤖"

    # Save AI reply
    ai_msg = Message(
        user_id=current_user.id,
        character=character,
        sender='ai',
        content=ai_reply
    )
    db.session.add(ai_msg)

    # Deduct one message
    current_user.remaining_messages -= 1
    db.session.commit()

    return jsonify({"reply": ai_reply})


# WATCHED 5 ADS → GRANT 15 MESSAGES
@auth.route('/ads-reward', methods=['POST'])
@login_required
def ads_reward():
    try:
        # ✅ Ensure ads_watched is never None
        if current_user.ads_watched is None:
            current_user.ads_watched = 0

        current_user.ads_watched += 1

        if current_user.ads_watched >= 5:
            if current_user.remaining_messages is None:
                current_user.remaining_messages = 0
            current_user.remaining_messages += 15
            current_user.ads_watched = 0
            db.session.commit()
            return jsonify({
                "message": "You earned more free chats!",
                "messages_added": True
            })

        db.session.commit()
        return jsonify({
            "message": "Ad watched. Keep going!",
            "ads_watched": current_user.ads_watched,
            "messages_added": False
        })

    except Exception as e:
        import traceback
        print("Ad reward error:", e)
        traceback.print_exc()
        return jsonify({"message": "Server error occurred."}), 500

# ADS STATUS
@auth.route('/ad-status')
@login_required
def ad_status():
    return jsonify({
        "remaining_messages": current_user.remaining_messages,
        "ads_watched": current_user.ads_watched
    })


# 🔍 SEARCH PAGE
@auth.route('/search')
@login_required
def search_characters():
    characters = Character.query.all()
    return render_template('search.html', characters=characters)

# 🕓 CHAT HISTORY PAGE
@auth.route('/history')
@login_required
def chat_history():
    user_messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.id.desc()).all()

    history = {}
    for msg in user_messages:
        if msg.character not in history:
            history[msg.character] = []
        history[msg.character].append(msg)

    return render_template('history.html', history=history)

# 👤 ACCOUNT PAGE
@auth.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)

# ✏️ EDIT PROFILE
@auth.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.age = request.form['age']
        current_user.gender = request.form['gender']
        current_user.ai_preference = request.form['ai_preference']
        db.session.commit()
        flash("Profile updated!")
        return redirect(url_for('auth.account'))

    return render_template('edit_profile.html', user=current_user)

# 🔒 CHANGE PASSWORD
@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        if not check_password_hash(current_user.password, current_password):
            flash("Current password is incorrect.")
            return redirect(url_for('auth.change_password'))

        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Password changed successfully.")
        return redirect(url_for('auth.account'))

    return render_template('change_password.html')

# ➕ CREATE CHARACTER
@auth.route('/create-character', methods=['POST'])
@login_required
def create_character():
    name = request.form['name']
    desc = request.form['desc']
    gender = request.form['gender']
    tags = request.form.get('tags', '')
    appearance = request.form['appearance']
    img = "default.jpg"

    existing = Character.query.filter_by(name=name).first()
    if existing:
        flash("Character with this name already exists.")
        return redirect(url_for('chat_dashboard'))

    new_char = Character(
        name=name,
        desc=desc,
        gender=gender,
        tags=tags,
        appearance=appearance,
        img=img,
        creator_id=current_user.id
    )
    db.session.add(new_char)
    db.session.commit()
    flash("Character created successfully!")
    return redirect(url_for('chat_dashboard'))

# CHAT DASHBOARD
@auth.route('/chat')
@login_required
def chat_dashboard():
    if current_user.email == "admin@talkitive.ai":
        return redirect(url_for('admin.dashboard'))
    preference = current_user.ai_preference or 'female'
    characters = Character.query.filter_by(gender=preference).all()
    return render_template('chat.html', characters=characters)



