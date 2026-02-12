"""
Intentionally Vulnerable Flask Web Application
================================================
WARNING: This application contains DELIBERATE security vulnerabilities
for educational and authorized testing purposes ONLY.

DO NOT deploy this application on any public-facing server.
Run ONLY on localhost (127.0.0.1) for security testing practice.

Vulnerabilities included:
- SQL Injection (login and search forms)
- Reflected Cross-Site Scripting (XSS)
- Missing CSRF Protection
- Insecure Direct Object References (IDOR)
- Missing Security Headers
- Hardcoded Credentials
- Verbose Error Messages
- Session Misconfiguration
"""

import os
import sqlite3
from flask import (
    Flask, request, render_template, redirect,
    url_for, session, g, make_response
)
from database import init_db, get_db

app = Flask(__name__)

# VULNERABILITY: Hardcoded secret key (weak and predictable)
app.secret_key = 'supersecretkey123'

# VULNERABILITY: Debug mode enabled (exposes stack traces)
app.debug = True

# VULNERABILITY: No session timeout configuration
# VULNERABILITY: No secure cookie flags
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = None

DATABASE = os.path.join(os.path.dirname(__file__), 'vulnerable.db')


def get_database():
    """Get database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_database(exception):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# VULNERABILITY: No security headers middleware
# Missing headers: X-Frame-Options, Content-Security-Policy,
#   Strict-Transport-Security, X-Content-Type-Options,
#   X-XSS-Protection, Referrer-Policy, Permissions-Policy
# ---------------------------------------------------------------------------


@app.route('/')
def index():
    """Home page - redirects to login."""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page with SQL injection vulnerability.

    VULNERABILITY: SQL Injection
    - User input is concatenated directly into SQL query
    - No parameterized queries or input sanitization
    - Allows authentication bypass with payloads like:
      Username: ' OR '1'='1' --
      Password: anything
    """
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        db = get_database()

        # VULNERABILITY: Direct string concatenation in SQL query
        # This is intentionally vulnerable to SQL injection
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

        try:
            cursor = db.execute(query)
            user = cursor.fetchone()

            if user:
                # VULNERABILITY: Storing sensitive data in session without encryption
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('search'))
            else:
                # VULNERABILITY: Different error messages for invalid user vs invalid password
                # allows username enumeration
                error = 'Invalid username or password. Please try again.'
        except sqlite3.OperationalError as e:
            # VULNERABILITY: Verbose error message reveals database structure
            error = f'Database error: {str(e)}'

    # VULNERABILITY: No CSRF token in the form
    return render_template('login.html', error=error)


@app.route('/search', methods=['GET', 'POST'])
def search():
    """
    Search page with reflected XSS and SQL injection vulnerabilities.

    VULNERABILITY: Reflected XSS
    - User search input is reflected directly in the response
    - No output encoding or Content-Security-Policy header

    VULNERABILITY: SQL Injection
    - Search query is concatenated into SQL without sanitization
    """
    results = []
    search_query = ''

    if request.method == 'POST':
        search_query = request.form.get('query', '')

        db = get_database()

        # VULNERABILITY: SQL Injection in search query
        query = f"SELECT * FROM products WHERE name LIKE '%{search_query}%' OR description LIKE '%{search_query}%'"

        try:
            cursor = db.execute(query)
            results = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # VULNERABILITY: Verbose SQL error exposed to user
            results = []
            search_query = f"Error: {str(e)}"

    elif request.method == 'GET' and 'q' in request.args:
        search_query = request.args.get('q', '')

        db = get_database()

        # VULNERABILITY: SQL Injection via GET parameter
        query = f"SELECT * FROM products WHERE name LIKE '%{search_query}%'"

        try:
            cursor = db.execute(query)
            results = cursor.fetchall()
        except sqlite3.OperationalError as e:
            results = []
            search_query = f"Error: {str(e)}"

    # VULNERABILITY: Reflected XSS - search_query is rendered without escaping
    # in the template using the |safe filter
    response = make_response(
        render_template('search.html', results=results, query=search_query)
    )

    # VULNERABILITY: No security headers set on response
    return response


@app.route('/profile/<int:user_id>')
def profile(user_id):
    """
    User profile page with Insecure Direct Object Reference (IDOR).

    VULNERABILITY: IDOR
    - Any user can access any other user's profile by changing the ID
    - No authorization check to verify the logged-in user matches the profile
    - Exposes sensitive user data including email and role
    """
    db = get_database()

    # VULNERABILITY: No authorization check - any user_id can be accessed
    # Should verify session['user_id'] == user_id
    cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        return 'User not found', 404

    # VULNERABILITY: Exposing all user fields including sensitive ones
    return render_template('profile.html', user=user)


@app.route('/api/users')
def api_users():
    """
    API endpoint that exposes user data.

    VULNERABILITY: No authentication required for API access
    VULNERABILITY: Exposes all user data including passwords
    VULNERABILITY: No rate limiting
    """
    db = get_database()

    # VULNERABILITY: Exposing all user data without authentication
    cursor = db.execute('SELECT id, username, email, role, password FROM users')
    users = cursor.fetchall()

    user_list = []
    for user in users:
        user_list.append({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            # VULNERABILITY: Exposing passwords in API response
            'password': user['password']
        })

    return {'users': user_list}


@app.route('/admin')
def admin():
    """
    Admin panel with broken access control.

    VULNERABILITY: No authentication or authorization check
    - Anyone can access the admin panel
    - No role-based access control
    """
    db = get_database()
    cursor = db.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor2 = db.execute('SELECT * FROM products')
    products = cursor2.fetchall()

    # VULNERABILITY: Admin page accessible without authentication
    return f"""
    <html>
    <head><title>Admin Panel</title></head>
    <body>
        <h1>Admin Panel</h1>
        <h2>Users ({len(users.fetchall()) if hasattr(users, 'fetchall') else 'N/A'})</h2>
        <p>Total users in database: check /api/users for details</p>
        <h2>System Info</h2>
        <p>Database: {DATABASE}</p>
        <p>Debug Mode: {app.debug}</p>
        <p>Secret Key: {app.secret_key}</p>
        <a href="/">Back to Home</a>
    </body>
    </html>
    """


@app.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/robots.txt')
def robots():
    """
    VULNERABILITY: robots.txt reveals sensitive paths
    """
    content = """User-agent: *
Disallow: /admin
Disallow: /api/users
Disallow: /backup
Disallow: /config
Disallow: /.git
"""
    return content, 200, {'Content-Type': 'text/plain'}


@app.route('/backup')
def backup():
    """
    VULNERABILITY: Exposed backup directory listing
    """
    return """
    <html>
    <head><title>Backup Files</title></head>
    <body>
        <h1>Backup Directory</h1>
        <ul>
            <li><a href="#">database_backup_2024.sql</a></li>
            <li><a href="#">config_backup.tar.gz</a></li>
            <li><a href="#">users_export.csv</a></li>
        </ul>
    </body>
    </html>
    """


@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler."""
    return '<h1>404 - Page Not Found</h1><p>The requested page does not exist.</p>', 404


@app.errorhandler(500)
def internal_error(error):
    """
    VULNERABILITY: Verbose error handler exposes internal details
    """
    return f'<h1>500 - Internal Server Error</h1><p>Details: {str(error)}</p>', 500


if __name__ == '__main__':
    # Initialize the database with sample data
    init_db(DATABASE)

    print("=" * 70)
    print("  WARNING: INTENTIONALLY VULNERABLE APPLICATION")
    print("  This application contains deliberate security vulnerabilities.")
    print("  DO NOT expose this to any network. Localhost use ONLY.")
    print("=" * 70)
    print()
    print("  Starting vulnerable web application on http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop.")
    print()

    # VULNERABILITY: Running on all interfaces would be dangerous
    # Binding to 127.0.0.1 only for safety
    app.run(host='127.0.0.1', port=5000, debug=True)
