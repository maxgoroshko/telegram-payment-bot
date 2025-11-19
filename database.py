import sqlite3
from datetime import datetime

# Ensure the database file exists
conn = sqlite3.connect("payments.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    amount REAL,
    method TEXT,
    user TEXT
)
""")
conn.commit()
conn.close()


def add_payment(amount, method, user):
    conn = sqlite3.connect("payments.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO payments (date, amount, method, user) VALUES (?, ?, ?, ?)",
                   (now, amount, method, user))
    conn.commit()
    conn.close()


def get_monthly_report(month_str):
    conn = sqlite3.connect("payments.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM payments WHERE strftime('%Y-%m', date) = ?
    """, (month_str,))
    rows = cursor.fetchall()
    conn.close()
    return rows
