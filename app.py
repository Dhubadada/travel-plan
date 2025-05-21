from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Better secret key generation

# Database setup
def get_db_connection():
    conn = sqlite3.connect('wanderlust.db')
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                destination TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (trip_id) REFERENCES trips (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                due_date TEXT,
                FOREIGN KEY (trip_id) REFERENCES trips (id)
            )
        ''')
        conn.commit()

# Initialize database at app startup
with app.app_context():
    init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template('homepage.html', logged_in='user_id' in session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                              (username, email, hashed_password))
                conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

# Trip routes
@app.route('/trips')
@login_required
def trips():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trips WHERE user_id = ?', (session['user_id'],))
        trips = cursor.fetchall()
    return render_template('trip.html', trips=trips, logged_in=True)

@app.route('/add_trip', methods=['POST'])
@login_required
def add_trip():
    if request.method == 'POST':
        destination = request.form['destination']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        notes = request.form.get('notes', '')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO trips (user_id, destination, start_date, end_date, notes) VALUES (?, ?, ?, ?, ?)', 
                          (session['user_id'], destination, start_date, end_date, notes))
            conn.commit()
        flash('Trip added successfully!', 'success')
    
    return redirect(url_for('trips'))

# Expense routes
@app.route('/expenses')
@login_required
def expenses():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trips WHERE user_id = ?', (session['user_id'],))
        trips = cursor.fetchall()
        
        cursor.execute('''
            SELECT expenses.*, trips.destination 
            FROM expenses 
            JOIN trips ON expenses.trip_id = trips.id 
            WHERE trips.user_id = ?
        ''', (session['user_id'],))
        expenses = cursor.fetchall()
    
    return render_template('expense.html', expenses=expenses, trips=trips, logged_in=True)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        trip_id = request.form['trip_id']
        category = request.form['category']
        amount = float(request.form['amount'])
        description = request.form.get('description', '')
        date = request.form['date']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO expenses (trip_id, category, amount, description, date) VALUES (?, ?, ?, ?, ?)', 
                          (trip_id, category, amount, description, date))
            conn.commit()
        flash('Expense added successfully!', 'success')
    
    return redirect(url_for('expenses'))

# Todo routes - made consistent
@app.route('/todos')
@login_required
def todos():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trips WHERE user_id = ?', (session['user_id'],))
        trips = cursor.fetchall()
        
        cursor.execute('''
            SELECT todos.*, trips.destination 
            FROM todos 
            JOIN trips ON todos.trip_id = trips.id 
            WHERE trips.user_id = ?
        ''', (session['user_id'],))
        todos = cursor.fetchall()
    
    return render_template('todo.html', todos=todos, trips=trips, logged_in=True)

@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    if request.method == 'POST':
        trip_id = request.form['trip_id']
        task = request.form['task']
        due_date = request.form.get('due_date', None)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO todos (trip_id, task, due_date) VALUES (?, ?, ?)', 
                          (trip_id, task, due_date))
            conn.commit()
        flash('Task added successfully!', 'success')
    
    return redirect(url_for('todos'))

# Map route
@app.route('/map')
@login_required
def map():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trips WHERE user_id = ?', (session['user_id'],))
        trips = cursor.fetchall()
    return render_template('map.html', trips=trips, logged_in=True)

# About route
@app.route('/about')
def about():
    return render_template('about.html', logged_in='user_id' in session)

if __name__ == '__main__':
    app.run(debug=True)