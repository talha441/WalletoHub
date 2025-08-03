from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import smtplib
import random
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'secretkey123'

# ---------------- DB INIT ------------------
def init_db():
    conn = sqlite3.connect('wallet.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        balance REAL DEFAULT 0.0,
        refer_code TEXT,
        referred_by TEXT,
        verified INTEGER DEFAULT 0,
        verification_code TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ----------------- EMAIL SEND FUNCTION ------------------
def send_verification_email(to_email, code):
    msg = MIMEText(f"Your verification code is: {code}")
    msg['Subject'] = 'Verify Your Email - Team CSB'
    msg['From'] = 'noreply@teamcsb.com'
    msg['To'] = to_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login('your_email@gmail.com', 'your_app_password')
            smtp.send_message(msg)
    except Exception as e:
        print("Email failed:", e)

# ---------------- ROUTES ------------------
@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        referred_by = request.form.get('referred_by')
        refer_code = email.split('@')[0] + str(random.randint(100, 999))
        verification_code = str(random.randint(100000, 999999))

        conn = sqlite3.connect('wallet.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, refer_code, referred_by, verification_code) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, email, password, refer_code, referred_by, verification_code))
            conn.commit()
            send_verification_email(email, verification_code)
        except sqlite3.IntegrityError:
            return "Email already registered."
        conn.close()
        session['pending_email'] = email
        return redirect('/verify')
    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'pending_email' not in session:
        return redirect('/login')

    if request.method == 'POST':
        code = request.form['code']
        email = session['pending_email']
        conn = sqlite3.connect('wallet.db')
        c = conn.cursor()
        c.execute("SELECT verification_code FROM users WHERE email = ?", (email,))
        result = c.fetchone()
        if result and result[0] == code:
            c.execute("UPDATE users SET verified = 1 WHERE email = ?", (email,))

            # Give referral bonus
            c.execute("SELECT referred_by FROM users WHERE email = ?", (email,))
            ref = c.fetchone()[0]
            if ref:
                c.execute("UPDATE users SET balance = balance + 1.0 WHERE refer_code = ?", (ref,))

            conn.commit()
            session.pop('pending_email', None)
            return redirect('/login')
        conn.close()
        return "Invalid verification code."

    return render_template('verify.html')

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
            if user[7] != 1:
                session['pending_email'] = email
                return redirect('/verify')
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
    c.execute("SELECT name, balance, refer_code FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    return render_template('dashboard.html', name=user[0], balance=user[1], refer_code=user[2])

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
