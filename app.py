from flask import Flask, render_template, redirect, url_for, request
from models import db, User, Message, Character  # ✅ include Character
from flask_login import LoginManager, current_user, login_required
from flask import send_from_directory
from admin.routes import admin
from flask_migrate import Migrate
from auth.routes import auth
from models import Character
from main.routes import main
import random


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://apnibaaty_user:oXXlekAtABIhqVaONZvztpvext6rdDmr@dpg-d1j07a7diees73cfi9pg-a.singapore-postgres.render.com/apnibaaty_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('.', 'ads.txt', mimetype='text/plain')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(main)
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat_dashboard'))
    return render_template('index.html')

from models import Character
import random

@app.route('/chat')
@login_required
def chat_dashboard():
    if not current_user.age or not current_user.gender or not current_user.ai_preference:
        return render_template('index.html', show_profile_popup=True)

    # Load characters from database based on preference
    preferred_gender = current_user.ai_preference.lower()
    characters = Character.query.filter_by(gender=preferred_gender).all()

    # Shuffle and pick top 6 for recommendations
    random.shuffle(characters)
    recommended_characters = characters[:6]

    return render_template('chat.html', characters=recommended_characters)


@app.route('/chat/<character>', methods=['GET', 'POST'])
@login_required
def character_chat(character):
    from datetime import datetime

    messages = Message.query.filter_by(user_id=current_user.id, character=character).all()
    char = Character.query.filter_by(name=character).first()
    character_img = char.img if char else "default.jpg"

    if request.method == 'POST':
        message_text = request.form.get("message")
        if message_text:
            db.session.add(Message(
                sender="user",
                content=message_text,
                character=character,
                user_id=current_user.id
            ))
            db.session.add(Message(
                sender="ai",
                content="This is a sample AI reply. (AI logic coming soon 🤖)",
                character=character,
                user_id=current_user.id
            ))
            db.session.commit()
        return redirect(url_for('character_chat', character=character))

    return render_template(
        'chat_room.html',
        character_name=character,
        character_img=character_img,
        character=character,
        messages=messages
    )

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
