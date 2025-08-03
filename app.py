from flask import Flask, render_template, request, redirect, session, url_for
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

users = {}
withdraw_requests = []

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        refer = request.form.get('refer')

        if email in users:
            return "User already exists"

        balance = 1.0 if refer in users else 0.0
        users[email] = {'password': password, 'balance': balance, 'refer': refer}
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.get(email)

        if user and user['password'] == password:
            session['user'] = email
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    user = users[session['user']]
    return render_template('dashboard.html', user_email=session['user'], balance=user['balance'])

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        method = request.form['method']
        number = request.form['number']
        amount = float(request.form['amount'])
        proof = request.files['proof']
        filename = secure_filename(proof.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        proof.save(filepath)

        withdraw_requests.append({
            'email': session['user'],
            'method': method,
            'number': number,
            'amount': amount,
            'proof': filepath,
            'status': 'Pending',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        return redirect('/dashboard')
    return render_template('withdraw.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        amount = float(request.form['amount'])
        if email in users:
            users[email]['balance'] += amount
    return render_template('admin.html', users=users, withdrawals=withdraw_requests)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
