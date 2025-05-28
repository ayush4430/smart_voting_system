from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# --- Flask Application Setup ---
app = Flask(__name__)

# --- Database Configuration ---
DATABASE = 'smart_voting.db'

# --- Database Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Call init_db() once when the application starts
with app.app_context():
    init_db()

# --- Routes (Web Pages) ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        password = request.form['password']

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO voters (voter_id, password) VALUES (?, ?)", (voter_id, password))
            conn.commit()
            return "Registration successful! You can now log in."
        except sqlite3.IntegrityError:
            conn.rollback()
            return "Registration failed: Voter ID already exists. Please choose a different one."
        finally:
            conn.close()
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        password = request.form['password']

        conn = get_db_connection()
        voter = conn.execute("SELECT * FROM voters WHERE voter_id = ? AND password = ?", (voter_id, password)).fetchone()
        conn.close()

        if voter:
            print(f"User '{voter_id}' logged in successfully.")
            return f"Login successful for {voter['voter_id']}!"
        else:
            return "Login failed. Invalid Voter ID or Password."
    else:
        return render_template('login.html')

# NEW CODE BELOW: Display All Registered Voters
@app.route('/voters_list')
def voters_list():
    conn = get_db_connection()
    # Fetch all rows from the 'voters' table
    voters = conn.execute("SELECT id, voter_id FROM voters").fetchall() # Fetches all rows as a list of Row objects
    conn.close()
    # Pass the list of voters to the HTML template
    return render_template('voters_list.html', voters=voters)

# --- Run Flask Application ---
if __name__ == '__main__':
    app.run(debug=True)
