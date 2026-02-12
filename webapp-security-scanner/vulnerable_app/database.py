"""
Database Setup Module for the Vulnerable Web Application
==========================================================
Creates an SQLite database with sample data for testing.
Passwords are stored in plaintext intentionally (vulnerability demonstration).

WARNING: This database configuration is intentionally insecure.
Do not use these patterns in production applications.
"""

import sqlite3
import os


def init_db(db_path):
    """
    Initialize the SQLite database with tables and sample data.

    Creates the following tables:
    - users: User accounts with plaintext passwords (intentionally insecure)
    - products: Sample product catalog for search testing
    - orders: Sample orders linked to users (for IDOR testing)
    - audit_log: Empty audit log table (intentionally not used)

    Args:
        db_path: Path to the SQLite database file
    """
    # Remove existing database to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # -----------------------------------------------------------------------
    # Users table
    # VULNERABILITY: Passwords stored in plaintext (no hashing)
    # VULNERABILITY: No password complexity requirements
    # VULNERABILITY: No account lockout mechanism
    # -----------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            full_name TEXT,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Sample users with plaintext passwords
    sample_users = [
        ('admin', 'admin123', 'admin@example.com', 'admin',
         'System Administrator', '+1-555-0100', '123 Admin St, Server City'),
        ('john_doe', 'password123', 'john@example.com', 'user',
         'John Doe', '+1-555-0101', '456 User Ave, Client Town'),
        ('jane_smith', 'letmein', 'jane@example.com', 'user',
         'Jane Smith', '+1-555-0102', '789 Main Blvd, Data Valley'),
        ('bob_wilson', 'qwerty', 'bob@example.com', 'moderator',
         'Bob Wilson', '+1-555-0103', '321 Oak Lane, Web Harbor'),
        ('alice_jones', 'password1', 'alice@example.com', 'user',
         'Alice Jones', '+1-555-0104', '654 Pine Road, Port City'),
        ('charlie_brown', 'abc123', 'charlie@example.com', 'user',
         'Charlie Brown', '+1-555-0105', '987 Elm Street, Net Town'),
        ('david_clark', 'iloveyou', 'david@example.com', 'user',
         'David Clark', '+1-555-0106', '147 Birch Way, Cloud City'),
        ('eve_martinez', 'welcome1', 'eve@example.com', 'user',
         'Eve Martinez', '+1-555-0107', '258 Cedar Drive, Host Village'),
        ('frank_taylor', '123456', 'frank@example.com', 'user',
         'Frank Taylor', '+1-555-0108', '369 Maple Court, Byte Town'),
        ('grace_lee', 'monkey', 'grace@example.com', 'user',
         'Grace Lee', '+1-555-0109', '741 Willow Path, Stack City'),
    ]

    cursor.executemany('''
        INSERT INTO users (username, password, email, role, full_name, phone, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sample_users)

    # -----------------------------------------------------------------------
    # Products table for search functionality testing
    # -----------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            stock INTEGER DEFAULT 0,
            sku TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    sample_products = [
        ('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver, 1600 DPI optical sensor',
         29.99, 'Electronics', 150, 'WM-001'),
        ('Mechanical Keyboard', 'Full-size mechanical keyboard with Cherry MX Blue switches and RGB backlight',
         89.99, 'Electronics', 75, 'MK-002'),
        ('USB-C Hub', '7-in-1 USB-C hub with HDMI, USB 3.0, SD card reader, and PD charging',
         49.99, 'Electronics', 200, 'UC-003'),
        ('Laptop Stand', 'Adjustable aluminum laptop stand for improved ergonomics and airflow',
         39.99, 'Accessories', 120, 'LS-004'),
        ('Webcam HD', '1080p HD webcam with built-in microphone and auto-focus for video conferencing',
         59.99, 'Electronics', 90, 'WC-005'),
        ('Monitor Light Bar', 'LED monitor light bar with adjustable color temperature and brightness',
         44.99, 'Lighting', 60, 'ML-006'),
        ('Cable Management Kit', 'Complete cable management solution with clips, ties, and sleeves',
         19.99, 'Accessories', 300, 'CM-007'),
        ('Desk Pad', 'Extra-large leather desk pad with non-slip base, 35x17 inches',
         24.99, 'Accessories', 180, 'DP-008'),
        ('Bluetooth Speaker', 'Portable Bluetooth 5.0 speaker with 12-hour battery life and IPX7 waterproof',
         34.99, 'Audio', 110, 'BS-009'),
        ('Noise Cancelling Headphones', 'Over-ear active noise cancelling headphones with 30-hour battery',
         149.99, 'Audio', 45, 'NC-010'),
        ('Surge Protector', '8-outlet surge protector with USB ports and 2100 joules protection rating',
         27.99, 'Electronics', 250, 'SP-011'),
        ('Ergonomic Chair Cushion', 'Memory foam seat cushion with cooling gel for all-day comfort',
         34.99, 'Furniture', 85, 'EC-012'),
        ('External SSD 1TB', 'Portable 1TB SSD with USB 3.2 Gen 2 interface and 1050 MB/s read speed',
         89.99, 'Storage', 65, 'ES-013'),
        ('Wireless Charger', 'Qi-certified 15W fast wireless charging pad compatible with all phones',
         22.99, 'Electronics', 170, 'WCH-014'),
        ('Privacy Screen Filter', '14-inch laptop privacy screen filter with anti-glare coating',
         32.99, 'Accessories', 95, 'PS-015'),
    ]

    cursor.executemany('''
        INSERT INTO products (name, description, price, category, stock, sku)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_products)

    # -----------------------------------------------------------------------
    # Orders table for IDOR testing
    # -----------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            shipping_address TEXT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    sample_orders = [
        (1, 2, 1, 89.99, 'shipped', '123 Admin St, Server City'),
        (2, 1, 2, 59.98, 'delivered', '456 User Ave, Client Town'),
        (2, 5, 1, 59.99, 'pending', '456 User Ave, Client Town'),
        (3, 10, 1, 149.99, 'processing', '789 Main Blvd, Data Valley'),
        (4, 3, 3, 149.97, 'shipped', '321 Oak Lane, Web Harbor'),
        (5, 8, 1, 24.99, 'delivered', '654 Pine Road, Port City'),
        (1, 13, 2, 179.98, 'pending', '123 Admin St, Server City'),
        (6, 6, 1, 44.99, 'shipped', '987 Elm Street, Net Town'),
        (3, 14, 1, 22.99, 'delivered', '789 Main Blvd, Data Valley'),
        (7, 9, 2, 69.98, 'processing', '147 Birch Way, Cloud City'),
    ]

    cursor.executemany('''
        INSERT INTO orders (user_id, product_id, quantity, total_price, status, shipping_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_orders)

    # -----------------------------------------------------------------------
    # Audit log table (intentionally empty - vulnerability: no logging)
    # -----------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # -----------------------------------------------------------------------
    # Sessions table for session management (intentionally insecure)
    # -----------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

    print(f"[+] Database initialized at: {db_path}")
    print(f"[+] Created tables: users, products, orders, audit_log, sessions")
    print(f"[+] Inserted {len(sample_users)} sample users")
    print(f"[+] Inserted {len(sample_products)} sample products")
    print(f"[+] Inserted {len(sample_orders)} sample orders")


def get_db(db_path):
    """
    Get a database connection.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        sqlite3.Connection: Database connection with Row factory
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == '__main__':
    # When run directly, initialize the database in the current directory
    db_file = os.path.join(os.path.dirname(__file__), 'vulnerable.db')
    init_db(db_file)
    print("\n[+] Database setup complete. You can now run the vulnerable app.")
