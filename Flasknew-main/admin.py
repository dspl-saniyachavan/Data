from app import app, db
from models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

with app.app_context():
    password = bcrypt.generate_password_hash("admin123").decode("utf-8")
    admin = User(username="admin", password=password, role="admin")
    db.session.add(admin)
    db.session.commit()

    print("Admin user created successfully")