from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'walletohubsecretkey'

# Database Initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            balance REAL DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            method TEXT,
            number TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

# Home
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            return redirect('/login')
        except:
            return "User already exists."
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE id=?", (session['user_id'],))
    balance = c.fetchone()[0]
    c.execute("SELECT * FROM withdrawals WHERE user_id=?", (session['user_id'],))
    withdrawals = c.fetchall()
    return render_template('dashboard.html', balance=balance, withdrawals=withdrawals)

# Withdraw
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        method = request.form['method']
        number = request.form['number']
        amount = float(request.form['amount'])
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO withdrawals (user_id, method, number, amount) VALUES (?, ?, ?, ?)",
                  (session['user_id'], method, number, amount))
        conn.commit()
        conn.close()
        return "✅ Withdrawal request submitted!"
    return render_template('withdraw.html')

# Admin Panel
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        amount = float(request.form['amount'])
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE email = ?", (amount, email))
        conn.commit()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM withdrawals WHERE status='pending'")
    withdrawals = c.fetchall()
    return render_template('admin.html', withdrawals=withdrawals)

# Mark Withdraw Complete
@app.route('/admin/complete/<int:withdraw_id>', methods=['POST'])
def complete_withdraw(withdraw_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE withdrawals SET status='completed' WHERE id=?", (withdraw_id,))
    conn.commit()
    return redirect('/admin')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Run the App
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
