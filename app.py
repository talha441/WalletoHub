**app.py**

```python
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wallet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    balance = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(10), unique=True)
    referred_by = db.Column(db.String(10))

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gateway = db.Column(db.String(50))
    account = db.Column(db.String(100))
    amount = db.Column(db.Float)
    status = db.Column(db.String(50), default='Pending')

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        referral_code = str(uuid.uuid4())[:8]
        referred_by = request.form.get('referral_code')

        new_user = User(username=username, email=email, password=password,
                        referral_code=referral_code, referred_by=referred_by)
        db.session.add(new_user)
        db.session.commit()

        # Referral bonus
        if referred_by:
            ref_user = User.query.filter_by(referral_code=referred_by).first()
            if ref_user:
                ref_user.balance += 1.0
                db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    referred_count = User.query.filter_by(referred_by=user.referral_code).count()
    return render_template('dashboard.html', user=user, referred_count=referred_count)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        gateway = request.form['gateway']
        account = request.form['account']
        amount = float(request.form['amount'])
        user = User.query.get(session['user_id'])
        if user.balance >= amount:
            withdrawal = Withdrawal(user_id=user.id, gateway=gateway, account=account, amount=amount)
            user.balance -= amount
            db.session.add(withdrawal)
            db.session.commit()
            flash('Withdrawal request submitted!', 'success')
        else:
            flash('Insufficient balance.', 'danger')
    return render_template('withdraw.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        amount = float(request.form['amount'])
        user = User.query.filter_by(email=email).first()
        if user:
            user.balance += amount
            db.session.commit()
            flash('Balance credited successfully!', 'success')
        else:
            flash('User not found.', 'danger')
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
```
