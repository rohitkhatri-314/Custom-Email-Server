import logging
import sqlite3

def init_database():
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT,
            message TEXT,
            received_date TEXT,
            received_time TEXT,
            size INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database initialized")

init_database()

