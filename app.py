# app.py

# --- 1. Import necessary modules ---
# Flask: The web framework that helps us build the web application.
# render_template: Used to send HTML files back to the user's browser.
# request: Allows us to access data sent from web forms (like text inputs).
# redirect: Used to send the user's browser to a different URL.
# url_for: Helps generate URLs for our routes dynamically, making links robust.
# flash: Used to show temporary messages to the user (e.g., "Voter registered successfully!").
from flask import Flask, render_template, request, redirect, url_for, flash

# sqlite3: Python's built-in module for interacting with SQLite databases.
import sqlite3

# --- 2. Initialize the Flask application ---
# This creates the main Flask app instance. '__name__' helps Flask locate resources.
app = Flask(__name__)

# --- 3. Configure the application ---
# SECRET_KEY: Required for Flask's flash messages (and other secure features like sessions).
# IMPORTANT: In a real application, this should be a very long, random, and secret string!
# For now, you can keep a simple one, but remember its purpose.
app.config['SECRET_KEY'] = 'your_super_secret_key_123' # **CHANGE THIS IN A REAL PROJECT!**

# --- 4. Database Configuration ---
# DATABASE: Defines the name of our SQLite database file. It will be created in your
# project folder if it doesn't already exist.
DATABASE = 'smart_voting.db'

# --- 5. Database Connection Helper Function ---
# This function provides a consistent way to connect to our database.
def get_db_connection():
    # Connects to the SQLite database file.
    conn = sqlite3.connect(DATABASE)
    # sqlite3.Row: Configures the connection to return rows as dictionary-like objects.
    # This means you can access columns by name (e.g., row['name']) instead of by index (e.g., row[0]),
    # making your code much more readable.
    conn.row_factory = sqlite3.Row
    return conn

# --- 6. Database Initialization Function ---
# This function creates our database tables if they don't already exist.
# It runs once when the application starts.
def init_db():
    # Get a database connection.
    conn = get_db_connection()
    # Get a cursor object, which allows us to execute SQL commands.
    cursor = conn.cursor()
    print("Initializing database...") # Print a message to the console for debugging

    # --- SQL Commands to Create Tables ---
    # CREATE TABLE IF NOT EXISTS: Ensures the table is only created if it doesn't exist yet,
    # preventing errors if you run init_db multiple times.
    # INTEGER PRIMARY KEY AUTOINCREMENT: A unique number for each row, automatically increases.
    # TEXT NOT NULL: Text data that cannot be empty.
    # UNIQUE: Ensures values in this column are unique across all rows (e.g., no two elections with the same name).
    # DEFAULT 0: Sets a default value if none is provided.
    # FOREIGN KEY: Links records in one table to records in another table (e.g., a candidate belongs to an election).

    # Table for different election types (e.g., Lok Sabha, Nagar Panchayat)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,       -- e.g., "Lok Sabha Elections 2024"
            type TEXT NOT NULL,             -- e.g., "Lok Sabha", "Nagar Panchayat"
            start_date TEXT,                -- Date in YYYY-MM-DD format (can be null)
            end_date TEXT,                  -- Date in YYYY-MM-DD format (can be null)
            is_active BOOLEAN NOT NULL DEFAULT 0 -- 0 for False, 1 for True (SQLite uses INTEGER for BOOLEAN)
        )
    ''')

    # Table for registered voters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT NOT NULL UNIQUE,  -- Unique ID for the voter (e.g., Aadhaar number or custom ID)
            name TEXT NOT NULL,
            email TEXT UNIQUE,              -- Email should also be unique if provided
            phone TEXT,                     -- Phone number (can be null)
            face_embedding TEXT,            -- Placeholder for face recognition data (e.g., a long string of numbers)
            has_voted INTEGER DEFAULT 0     -- 0: Not voted, 1: Voted (for the current election cycle conceptually)
        )
    ''')

    # Table for candidates (each candidate is linked to a specific election)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER NOT NULL,   -- Foreign Key linking to the 'elections' table
            name TEXT NOT NULL,
            party TEXT,
            vote_count INTEGER DEFAULT 0,
            FOREIGN KEY (election_id) REFERENCES elections (id)
        )
    ''')

    # Table to record each individual vote (important for audit trail and preventing double voting)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER NOT NULL,
            voter_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, -- Records when the vote was cast
            FOREIGN KEY (election_id) REFERENCES elections (id),
            FOREIGN KEY (voter_id) REFERENCES voters (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    ''')

    conn.commit() # Save the changes (table creations) to the database file. Crucial!
    conn.close()  # Close the database connection. Always close connections when done.

# --- 7. Flask Routes (Define how URLs respond) ---
# These functions define what happens when a user visits a specific URL in their browser.
# All route functions should be defined here, before the 'if __name__ == "__main__":' block.

# Home page route: Accessible at the root URL (e.g., http://127.0.0.1:5000/)
@app.route('/')
def home():
    # Renders the 'index.html' template and sends it to the browser.
    return render_template('index.html')

# Add Election route: Accessible at /add_election
# methods=('GET', 'POST'): This route handles both:
#   - GET requests (when you first load the page to see the empty form).
#   - POST requests (when you submit the form data).
@app.route('/add_election', methods=('GET', 'POST'))
def add_election():
    # Check if the request method is POST (meaning the form was submitted).
    if request.method == 'POST':
        # Retrieve data from the form fields using their 'name' attributes.
        name = request.form['name']
        type = request.form['type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Basic server-side validation: Check if required fields are not empty.
        if not name or not type:
            # Flash an error message if validation fails.
            flash('Election Name and Type are required!', 'error')
        else:
            conn = get_db_connection() # Get a database connection
            try:
                # DAA - Data Persistence (Insert Operation):
                # Execute an SQL INSERT command to add the new election to the 'elections' table.
                # The '?' are placeholders for the data, which is passed as a tuple.
                conn.execute('INSERT INTO elections (name, type, start_date, end_date) VALUES (?, ?, ?, ?)',
                            (name, type, start_date, end_date))
                conn.commit() # Commit the changes to save them permanently to the database.
                flash(f'Election "{name}" added successfully!', 'success') # Success message
                # Redirect the user to the list of elections after successful addition.
                # url_for('list_elections') generates the URL for the 'list_elections' function/route.
                return redirect(url_for('list_elections'))
            # Handle cases where a unique constraint is violated (e.g., trying to add an election with an existing name).
            except sqlite3.IntegrityError:
                flash(f'Error: Election with name "{name}" already exists. Please choose a different name.', 'error')
            finally:
                conn.close() # Always close the connection, even if an error occurs.

    # If it's a GET request (or if POST failed), render the form page.
    return render_template('add_election.html')

# List Elections route: Accessible at /elections
@app.route('/elections')
def list_elections():
    conn = get_db_connection() # Get a database connection
    # DAA - Data Retrieval (Select Operation):
    # Execute an SQL SELECT command to fetch all records from the 'elections' table.
    # .fetchall() retrieves all rows from the query result.
    elections = conn.execute('SELECT * FROM elections').fetchall()
    conn.close() # Close the connection
    # Render the 'list_elections.html' template and pass the fetched 'elections' data to it.
    # This data can then be looped through and displayed in the HTML.
    return render_template('list_elections.html', elections=elections)

# Register Voter route: Accessible at /register_voter
@app.route('/register_voter', methods=('GET', 'POST'))
def register_voter():
    if request.method == 'POST':
        # Retrieve voter data from the form.
        voter_id = request.form['voter_id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        # Server-side validation for required fields.
        if not voter_id or not name:
            flash('Voter ID and Name are required!', 'error')
        else:
            conn = get_db_connection() # Get connection
            try:
                # DAA - Data Persistence (Insert Operation):
                # Insert new voter data into the 'voters' table.
                conn.execute('INSERT INTO voters (voter_id, name, email, phone) VALUES (?, ?, ?, ?)',
                            (voter_id, name, email, phone))
                conn.commit() # Commit changes
                flash(f'Voter "{name}" ({voter_id}) registered successfully!', 'success')
                return redirect(url_for('list_voters')) # Redirect to voter list
            # Handle unique constraint errors (e.g., duplicate voter_id or email).
            except sqlite3.IntegrityError as e:
                # You can make these error messages more specific if needed
                # by parsing 'e' but a general message is fine for now.
                # Example: if "voter_id" in str(e): ...
                if "voter_id" in str(e).lower(): # Check if error message contains "voter_id"
                     flash(f'Error: Voter with ID "{voter_id}" already exists.', 'error')
                elif "email" in str(e).lower(): # Check if error message contains "email"
                     flash(f'Error: Email "{email}" is already registered.', 'error')
                else:
                    flash(f'Error: Could not register voter. Possible duplicate entry or other database issue.', 'error')
            finally:
                conn.close() # Close connection
    return render_template('register_voter.html')

# List Voters route: Accessible at /voters
@app.route('/voters')
def list_voters():
    conn = get_db_connection() # Get connection
    # DAA - Data Retrieval (Select Operation):
    # Fetch all records from the 'voters' table.
    voters = conn.execute('SELECT * FROM voters').fetchall()
    conn.close() # Close connection
    # Render the 'list_voters.html' template and pass the fetched 'voters' data.
    return render_template('list_voters.html', voters=voters)


# --- 8. Main Application Entry Point ---
# This block ensures that the 'init_db()' function and 'app.run()' are
# called only when you execute this script directly (e.g., 'python app.py').
# It won't run if this file is imported as a module into another script.
if __name__ == '__main__':
    init_db() # Initialize the database tables before starting the web server.
    app.run(debug=True) # Start the Flask development server.
                        # debug=True enables automatic reloading and a debugger for easier development.
                        # **IMPORTANT: Set debug=False in production (real, live websites)!**