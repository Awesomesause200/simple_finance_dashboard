from authlib.integrations.flask_client import OAuth
from flask import url_for
import hashlib
import os
from . import db
from .models import User

oauth = OAuth()
google = oauth.register(
    name='google',
    client_id='GOOGLE_CLIENT_ID',
    client_secret='GOOGLE_CLIENT_SECRET',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/oauth2/v3/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)


# Temporarily use local oAuth instead of google oAuth
def hash_password(password: str, salt: bytes = None) -> tuple:
    if salt is None:
        salt = os.urandom(16)  # 16 bytes random salt
    pw_hash = hashlib.sha256(salt + password.encode()).hexdigest()
    return pw_hash, salt


def register_user(username, password):
    existing = User.query.filter_by(username=username).first()
    if existing:
        return False, "User already exists"
    pw_hash, salt = hash_password(password)
    user = User(username=username, password_hash=pw_hash, salt=salt)
    db.session.add(user)
    db.session.commit()
    return True, "User created"


def verify_password(user: User, password: str) -> bool:
    pw_hash, _ = hash_password(password, user.salt)
    return pw_hash == user.password_hash


