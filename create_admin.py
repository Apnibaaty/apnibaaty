from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    existing_admin = User.query.filter_by(email="apnibaaty@gmail.com").first()
    if not existing_admin:
        admin_user = User(
            name="Admin",
            email="apnibaaty@gmail.com",
            password=generate_password_hash("123456799"),
            age=25,
            gender="other",
            ai_preference="female",
            remaining_messages=100,
            ads_watched=0
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created successfully.")
    else:
        print("⚠️ Admin user already exists.")
