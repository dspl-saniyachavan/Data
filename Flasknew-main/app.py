
from flask_jwt_extended import get_jwt

from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from config import Config
from models import db, User
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token
)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# ---------------------------------
# Create Tables
# ---------------------------------


# ---------------------------------
# Login
# ---------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    refresh_token = create_refresh_token(
        identity=str(user.id)
    )

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200

from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()

    new_access_token = create_access_token(identity=user_id)

    return jsonify({
        "access_token": new_access_token
    }), 200
# ---------------------------------
# Register (ADMIN ONLY)
# ---------------------------------
@app.route("/register", methods=["POST"])
@jwt_required()
def register():
    from flask_jwt_extended import get_jwt

    claims = get_jwt()
    role = claims.get("role")

    if role != "admin":
        return jsonify({"message": "Admin access required"}), 403

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user = User(
        username=username,
        password=hashed_password,
        role=role
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

# ---------------------------------
# Protected Route (Any Auth User)
# ---------------------------------
@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    from flask_jwt_extended import get_jwt, get_jwt_identity

    user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")

    return jsonify({
        "user_id": user_id,
        "role": role
    })


# ---------------------------------
# Admin Only Route Example
# ---------------------------------
@app.route("/admin-only", methods=["GET"])
@jwt_required()
def admin_only():
    current_user = get_jwt_identity()

    if current_user["role"] != "admin":
        return jsonify({"message": "Admins only"}), 403

    return jsonify({"message": "Welcome Admin"}), 200

# from .models import User

@app.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 2, type=int)

    users = User.query.paginate(page=page, per_page=per_page)

    return {
        "users": [user.to_dict() for user in users.items],
        "total": users.total,
        "pages": users.pages,
        "current_page": users.page
    }


if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
