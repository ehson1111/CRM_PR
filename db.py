import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('crm_bot.db')
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        name TEXT,
        role TEXT DEFAULT 'support'
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        user_id INTEGER,
        amount REAL,
        stage TEXT,
        FOREIGN KEY (customer_id) REFERENCES Customers(id),
        FOREIGN KEY (user_id) REFERENCES Users(id)
    )
    """)
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('crm_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_user(telegram_id, name, role='support'):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (telegram_id, name, role) VALUES (?, ?, ?)", 
                      (telegram_id, name, role))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_customer(name, phone, email, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Customers (name, phone, email, status) VALUES (?, ?, ?, ?)",
                  (name, phone, email, status))
    conn.commit()
    customer_id = cursor.lastrowid
    conn.close()
    return customer_id

def get_customers(limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Customers ORDER BY created_at DESC LIMIT ?", (limit,))
    customers = cursor.fetchall()
    conn.close()
    return customers

def add_deal(customer_id, user_id, amount, stage):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Deals (customer_id, user_id, amount, stage) VALUES (?, ?, ?, ?)",
                  (customer_id, user_id, amount, stage))
    conn.commit()
    deal_id = cursor.lastrowid
    conn.close()
    return deal_id

def get_deals(user_id=None, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT Deals.*, Customers.name as customer_name 
            FROM Deals
            JOIN Customers ON Deals.customer_id = Customers.id
            WHERE user_id = ? 
            ORDER BY Deals.id DESC 
            LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT Deals.*, Customers.name as customer_name 
            FROM Deals
            JOIN Customers ON Deals.customer_id = Customers.id
            ORDER BY Deals.id DESC 
            LIMIT ?
        """, (limit,))
    deals = cursor.fetchall()
    conn.close()
    return deals

def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Customers")
    total_customers = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM Customers GROUP BY status")
    status_stats = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM Deals")
    total_deals = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM Deals WHERE stage = 'closed'")
    total_revenue = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_customers': total_customers,
        'status_stats': status_stats,
        'total_deals': total_deals,
        'total_revenue': total_revenue
    }