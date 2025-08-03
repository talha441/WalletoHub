from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

if not os.path.exists('wallet.db'):
    conn = sqlite3.connect('wallet.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, balance REAL DEFAULT 0, refer_code TEXT, referred_by TEXT)''')
    c.execute('''CREATE TABLE withdrawals (id INTEGER PRIMARY KEY, user_id INTEGER, method TEXT, number TEXT, amount REAL, status TEXT DEFAULT 'pending')''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('wallet.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        referred_by = request.form.get('referred_by') or None

        refer_code = str(uuid4())[:8]

        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (name, email, password, refer_code, referred_by) VALUES (?, ?, ?, ?, ?)', (name, email, password, refer_code, referred_by))
            conn.commit()

            if referred_by:
                c.execute('UPDATE users SET balance = balance + 1 WHERE refer_code = ?', (referred_by,))
                conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return 'Email already registered.'

        conn.close()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            return redirect('/dashboard')
        else:
            return 'Invalid credentials.'

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT name, balance, refer_code FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()

    return render_template('dashboard.html', name=user['name'], balance=user['balance'], refer_code=user['refer_code'])

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect('/login')

    success = False
    if request.method == 'POST':
        method = request.form['method']
        number = request.form['number']
        amount = float(request.form['amount'])

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
        balance = c.fetchone()['balance']

        if balance >= amount:
            c.execute('INSERT INTO withdrawals (user_id, method, number, amount) VALUES (?, ?, ?, ?)', (session['user_id'], method, number, amount))
            c.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, session['user_id']))
            conn.commit()
            success = True
        conn.close()

        return render_template('withdraw.html', success=success, amount=amount, method=method, number=number)

    return render_template('withdraw.html', success=False)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('email') != 'admin@gmail.com':
        return redirect('/login')

    message = None
    if request.method == 'POST':
        email = request.form['email']
        amount = float(request.form['amount'])

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance + ? WHERE email = ?', (amount, email))
        conn.commit()
        conn.close()
        message = f'Balance added to {email}'

    return render_template('admin.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
