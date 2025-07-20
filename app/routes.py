from flask import Blueprint, redirect, session, url_for, render_template, request, flash
from .oauth import google, oauth, verify_password, register_user, hash_password
from .models import db, User, Category, Transaction
from werkzeug.utils import secure_filename
import csv
from io import TextIOWrapper

bp = Blueprint('routes', __name__)


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    # redirect_uri = url_for('routes.auth', _external=True)
    # return google.authorize_redirect(redirect_uri)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and verify_password(user, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already taken")
            return render_template('register.html')

        # Hash password
        pw_hash, salt = hash_password(password)

        # Create user
        new_user = User(username=username, password_hash=pw_hash, salt=salt)
        db.session.add(new_user)
        db.session.commit()

        # Login the user
        session['user_id'] = new_user.id
        return redirect(url_for('routes.dashboard'))

    return render_template('register.html')


@bp.route('/auth')
def auth():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()

    # Create user if it doesn't exist
    user = User.query.filter_by(oauth_id=user_info['sub']).first()
    if not user:
        user = User(oauth_id=user_info['sub'], email=user_info['email'], oauth_provider='google')
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    return redirect(url_for('routes.dashboard'))


@bp.route('/dashboard')
def dashboard():
    # Example: sum expenses by category for logged-in user
    data = db.session.query(
        Category.name, db.func.sum(Transaction.amount)
    ).join(Transaction).filter_by(user_id=session['user_id']).group_by(Category.name).all()

    labels = [item[0] for item in data]
    values = [float(item[1]) for item in data]

    return render_template("dashboard.html", labels=labels, values=values)


@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('statement')
        if not file:
            flash("No file uploaded")
            return redirect(request.url)

        # Parse CSV
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.DictReader(stream)

        user_id = session.get('user_id')
        if not user_id:
            flash("You must be logged in")
            return redirect(url_for('routes.login'))

        row: dict  # for type hinting
        for row in csv_reader:
            try:
                amount = float(row['Amount'])
                date = row['Date']
                description = row['Description']
                category_name = row.get('Category', 'Uncategorized')

                # Get or create category
                category = Category.query.filter_by(name=category_name, user_id=user_id).first()
                if not category:
                    category = Category(name=category_name, user_id=user_id)
                    db.session.add(category)
                    db.session.commit()

                # Create transaction
                transaction = Transaction(
                    amount=amount,
                    date=date,
                    description=description,
                    type='expense' if amount < 0 else 'income',
                    user_id=user_id,
                    category_id=category.id
                )
                db.session.add(transaction)

            except Exception as e:
                print(f"Error processing row: {row} — {e}")
                continue

        db.session.commit()
        flash("Upload successful!")
        return redirect(url_for('routes.dashboard'))

    return render_template('upload.html')
