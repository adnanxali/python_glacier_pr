import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def get_db_connection():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image1_path TEXT NOT NULL,
            image2_path TEXT NOT NULL,
            area1 INTEGER,
            area2 INTEGER,
            intersection_area INTEGER,
            growth_area INTEGER,
            growth_percentage REAL,
            growth_status TEXT,
            risk_binary TEXT,
            risk_level TEXT,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM admin WHERE username = ?", (Config.ADMIN_USERNAME,))
    if cursor.fetchone()[0] == 0:
        admin_password_hash = generate_password_hash(Config.ADMIN_PASSWORD)
        cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", 
                      (Config.ADMIN_USERNAME, admin_password_hash))
    
    conn.commit()
    conn.close()

def create_user(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return dict(user)
    return None

def verify_admin(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE username = ?", (username,))
    admin = cursor.fetchone()
    conn.close()
    if admin and check_password_hash(admin['password'], password):
        return dict(admin)
    return None

def save_analysis(user_id, image1_path, image2_path, area1, area2, intersection_area, 
                 growth_area, growth_percentage, growth_status, risk_binary, risk_level, 
                 latitude=None, longitude=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO analyses (user_id, image1_path, image2_path, area1, area2, 
                            intersection_area, growth_area, growth_percentage, 
                            growth_status, risk_binary, risk_level, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, image1_path, image2_path, area1, area2, intersection_area, 
          growth_area, growth_percentage, growth_status, risk_binary, risk_level, 
          latitude, longitude))
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    return analysis_id

def get_user_analyses(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    analyses = cursor.fetchall()
    conn.close()
    return [dict(row) for row in analyses]

def get_all_analyses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses ORDER BY created_at DESC")
    analyses = cursor.fetchall()
    conn.close()
    return [dict(row) for row in analyses]

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    return [dict(row) for row in users]

def get_risk_distribution():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT risk_level, COUNT(*) as count, latitude, longitude 
        FROM analyses 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY latitude, longitude, risk_level
    ''')
    distribution = cursor.fetchall()
    conn.close()
    return [dict(row) for row in distribution]