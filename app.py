from flask import Flask, render_template, request, redirect, session
import mysql.connector
from datetime import date

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database initialization
db = mysql.connector.connect(
    host="localhost",
    user="your_username",
    password="your_password",
    database="your_database_name"
)
cursor = db.cursor()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM users WHERE username=%s', (username,))
        user = cursor.fetchone()
        if user and password == user[3]:
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)', (username, email, password))
        db.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cursor.execute('SELECT * FROM users WHERE id=%s', (user_id,))
    user = cursor.fetchone()
    cursor.execute('SELECT * FROM books')
    books = cursor.fetchall()
    return render_template('dashboard.html', user=user, books=books)

@app.route('/borrow/<int:book_id>')
def borrow_book(book_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cursor.execute('SELECT * FROM books WHERE id=%s', (book_id,))
    book = cursor.fetchone()
    if not book[5]:  # Checking if the book is available
        return redirect('/dashboard')
    cursor.execute('INSERT INTO loans (user_id, book_id, borrowed_date) VALUES (%s, %s, %s)', (user_id, book_id, date.today()))
    cursor.execute('UPDATE books SET available=0 WHERE id=%s', (book_id,))
    db.commit()
    return redirect('/dashboard')

@app.route('/return/<int:book_id>')
def return_book(book_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cursor.execute('SELECT * FROM loans WHERE user_id=%s AND book_id=%s AND returned_date IS NULL', (user_id, book_id))
    loan = cursor.fetchone()
    if loan:
        cursor.execute('UPDATE loans SET returned_date=%s WHERE id=%s', (date.today(), loan[0]))
        cursor.execute('UPDATE books SET available=1 WHERE id=%s', (book_id,))
        db.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
