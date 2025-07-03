from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    ai_preference = db.Column(db.String(10), nullable=True)
    oauth_provider = db.Column(db.String(50))
    is_premium = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)  # ✅ Add this field

    # 🆕 Added for monetization
    remaining_messages = db.Column(db.Integer, default=30)  # New users start with 30 messages
    ads_watched = db.Column(db.Integer, default=0)          # Count of ads watched in current cycle

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(10), nullable=False)  # "user" or "ai"
    content = db.Column(db.Text, nullable=False)
    character = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'sender': self.sender,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    desc = db.Column(db.Text, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    tags = db.Column(db.String(200), nullable=True)
    appearance = db.Column(db.Text, nullable=True)
    img = db.Column(db.String(200), default='default.jpg')
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
