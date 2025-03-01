from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Database initialization
DATABASE = 'orders.db'

def init_db():
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()

            # Create the new tables with the updated schema (excluding deletion of old table)
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            username TEXT NOT NULL,
                            password TEXT NOT NULL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY,
                            username TEXT NOT NULL,
                            items TEXT NOT NULL,
                            total_price REAL NOT NULL,
                            discount REAL NOT NULL,
                            date_time TEXT NOT NULL)''')
            conn.commit()
            print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

@app.route('/')
def index():
    # Check if the user is logged in (session management)
    if 'username' in session:
        return redirect(url_for('home'))  # Redirect to the home page if logged in
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()  # Close the connection after fetching the user
    
        if user:
            # Store the username in the session after successful login
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to the home page
        else:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('index'))  # Stay on the login page

    except Exception as e:
        print(f"Error during login: {str(e)}")
        flash('An error occurred while processing your request.', 'danger')
        return redirect(url_for('index'))  # Return to login page

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['new-username']
    password = request.form['new-password']
    
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        existing_user = c.fetchone()

        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            conn.close()
            return redirect(url_for('index'))  # Stay on the index page
        else:
            # Insert new user into the users table
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Signup successful! Please log in.', 'success')
            conn.close()  # Close the connection after commit
            return redirect(url_for('index'))  # Redirect to login page after signup
    except sqlite3.DatabaseError as e:
        print(f"Database error during signup: {str(e)}")  # Log database errors to the console
        flash('An error occurred while accessing the database. Please try again later.', 'danger')
    except Exception as e:
        print(f"General error during signup: {str(e)}")  # Log other types of errors
        flash('An error occurred during signup. Please try again.', 'danger')
    
    return redirect(url_for('index'))  # In case of error, stay on the signup page

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the user from the session
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))  # Redirect to the index page (login page)

@app.route('/home')
def home():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to the login page if not logged in
    return render_template('home.html')

@app.route('/about')
def about():
    # About page, accessible to all
    return render_template('about.html')

@app.route('/order', methods=['GET', 'POST'])
def order():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        items = request.form.get('items')  # Get the serialized list of items
        total_price = float(request.form.get('total_price', 0))  # Get total price after discount
        coupon_code = request.form.get('coupon_code')  # Get coupon code if any
        discount = 0

        if coupon_code == 'DISCOUNT10':
            discount = total_price * 0.1
        elif coupon_code == 'DISCOUNT20':
            discount = total_price * 0.2

        # Final total price after discount
        total_price_after_discount = total_price - discount

        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('''INSERT INTO orders (username, items, total_price, discount, date_time) 
                         VALUES (?, ?, ?, ?, ?)''', 
                         (session['username'], items, total_price_after_discount, discount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order'))
        except Exception as e:
            flash(f"An error occurred while placing your order: {str(e)}", 'danger')
            return redirect(url_for('order'))

    # Show available dishes
    dishes = [
        {"name": "Butter Naan with Curry", "price": 200, "img": "img1.jpg"},
        {"name": "Burger and Fries", "price": 250, "img": "img2.jpg"},
        {"name": "Macaroni Pasta", "price": 300, "img": "img3.jpg"},
        {"name": "Masala Idli", "price": 350, "img": "img4.jpg"},
        {"name": "Biryani", "price": 350, "img": "img5.jpg"},
        {"name": "Cheesy Pizza", "price": 350, "img": "img8.jpg"},
        {"name": "Chocolate Cake", "price": 350, "img": "img9.jpg"}
    ]

    return render_template('order.html', dishes=dishes)

@app.route('/apply_coupon', methods=['POST'])
def apply_coupon():
    coupon_code = request.form['coupon_code']
    discount = 0
    
    if coupon_code == 'DISCOUNT10':
        discount = 10  # 10% discount
    elif coupon_code == 'DISCOUNT20':
        discount = 20  # 20% discount
    
    return str(discount)  # Return the discount percentage to update the frontend

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
