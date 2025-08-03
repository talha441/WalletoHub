from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import smtplib
import random

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
        balance REAL DEFAULT 0.0,
        is_verified INTEGER DEFAULT 0,
        refer_code TEXT,
        referred_by TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS verifications (
        email TEXT,
        code TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def send_verification_email(to_email, code):
    # Use your SMTP settings
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('your-email@gmail.com', 'your-app-password')
        subject = "Verify your account"
        body = f"Your verification code is: {code}"
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail('your-email@gmail.com', to_email, message)
        server.quit()
    except:
        print("Email sending failed")

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

        conn = sqlite3.connect('wallet.db')
        c = conn.cursor()
        try:
            refer_code = f"CSB{random.randint(1000,9999)}"
            c.execute("INSERT INTO users (name, email, password, refer_code, referred_by) VALUES (?, ?, ?, ?, ?)",
                      (name, email, password, refer_code, referred_by))
            code = str(random.randint(100000, 999999))
            c.execute("INSERT INTO verifications (email, code) VALUES (?, ?)", (email, code))
            send_verification_email(email, code)
            conn.commit()
        except sqlite3.IntegrityError:
            return "Email already registered."
        conn.close()
        return redirect(url_for('verify_email', email=email))
    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify_email():
    email = request.args.get('email')
    if request.method == 'POST':
        code = request.form['code']
        conn = sqlite3.connect('wallet.db')
        c = conn.cursor()
        c.execute("SELECT * FROM verifications WHERE email = ? AND code = ?", (email, code))
        row = c.fetchone()
        if row:
            c.execute("UPDATE users SET is_verified = 1 WHERE email = ?", (email,))
            c.execute("DELETE FROM verifications WHERE email = ?", (email,))

            # Add referral bonus
            c.execute("SELECT referred_by FROM users WHERE email = ?", (email,))
            ref = c.fetchone()
            if ref and ref[0]:
                c.execute("UPDATE users SET balance = balance + 10 WHERE refer_code = ?", (ref[0],))

            conn.commit()
            conn.close()
            return redirect('/login')
        conn.close()
        return "Invalid verification code."
    return render_template('verify.html', email=email)

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
            if user[5] == 0:
                return redirect(url_for('verify_email', email=email))
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

@app.route('/support')
def support():
    return render_template('support.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
