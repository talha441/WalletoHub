from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Load users data
def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            return json.load(f)
    return {}

# Save users data
def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# Load withdrawals
def load_withdrawals():
    if os.path.exists('withdrawals.json'):
        with open('withdrawals.json', 'r') as f:
            return json.load(f)
    return []

# Save withdrawals
def save_withdrawals(withdrawals):
    with open('withdrawals.json', 'w') as f:
        json.dump(withdrawals, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        referral = request.form.get('referral', '')
        users = load_users()

        if email in users:
            return "User already exists"

        users[email] = {
            'password': password,
            'balance': 0.0,
            'referral': referral,
            'referred_users': [],
        }

        if referral and referral in users:
            users[referral]['balance'] += 1.0
            users[referral]['referred_users'].append(email)

        save_users(users)
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()

        if email in users and users[email]['password'] == password:
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    users = load_users()
    user = users.get(email, {})
    referral_link = f"https://{request.host}/register?referral={email}"
    referral_count = len(user.get('referred_users', []))

    return render_template('dashboard.html', email=email, balance=user.get('balance', 0.0),
                           referral_link=referral_link, referral_count=referral_count)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        gateway = request.form['gateway']
        account_number = request.form['account_number']
        amount = float(request.form['amount'])
        email = session['email']
        users = load_users()

        if users[email]['balance'] < amount:
            return "Insufficient balance"

        users[email]['balance'] -= amount
        save_users(users)

        withdrawals = load_withdrawals()
        withdrawals.append({
            'id': str(uuid.uuid4()),
            'email': email,
            'gateway': gateway,
            'account_number': account_number,
            'amount': amount,
            'status': 'Pending'
        })
        save_withdrawals(withdrawals)

        return "Withdrawal request submitted"

    return render_template('withdraw.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    users = load_users()
    withdrawals = load_withdrawals()

    if request.method == 'POST':
        action = request.form['action']
        target_email = request.form['email']
        amount = float(request.form['amount'])

        if action == 'credit' and target_email in users:
            users[target_email]['balance'] += amount
            save_users(users)

        elif action == 'complete_withdrawal':
            for w in withdrawals:
                if w['id'] == request.form['withdrawal_id']:
                    w['status'] = 'Completed'
                    break
            save_withdrawals(withdrawals)

    return render_template('admin.html', users=users, withdrawals=withdrawals)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
