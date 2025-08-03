from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secretkey123'

# Database setup
def init_db():
    conn = sqlite3.connect('wallet.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        balance REAL DEFAULT 0.0
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('wallet.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Email already registered."
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('wallet.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['email'] = user[2]
            return redirect('/dashboard')
        else:
            return "Invalid credentials."
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('wallet.db')
    c = conn.cursor()
    c.execute("SELECT name, balance FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    return render_template('dashboard.html', name=user[0], balance=user[1])

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        method = request.form['method']
        number = request.form['number']
        amount = float(request.form['amount'])

        return render_template('withdraw.html', success=True, method=method, number=number, amount=amount)
    return render_template('withdraw.html', success=False)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or session['email'] != 'admin@gmail.com':
        return redirect('/login')

    if request.method == 'POST':
        email = request.form['email']
        amount = float(request.form['amount'])

        conn = sqlite3.connect('wallet.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE email = ?", (amount, email))
        conn.commit()
        conn.close()
        return render_template('admin.html', message=f"{email} updated successfully!")

    return render_template('admin.html', message="")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
