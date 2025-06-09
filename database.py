import sqlite3
import json
from datetime import datetime
import hashlib
import pandas as pd

class Database:
    def __init__(self, db_path='smart_money_tracker.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts table with performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                email_sent BOOLEAN DEFAULT 0,
                alert_price REAL,
                price_1h REAL,
                price_1d REAL,
                price_1w REAL,
                return_1h REAL,
                return_1d REAL,
                return_1w REAL,
                is_successful BOOLEAN,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Watchlist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id INTEGER,
                symbol TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, symbol),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, email):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?)
            ''', (username, password_hash, email))
            conn.commit()
            return True, "User created successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, email FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result[0], result[1]  # Success, user_id, email
        return False, None, None
    
    def save_alert(self, user_id, symbol, alert_type, message, details, alert_price, email_sent=False):
        """Save a new alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (user_id, symbol, alert_type, message, details, alert_price, email_sent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, symbol, alert_type, message, json.dumps(details), alert_price, email_sent))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return alert_id
    
    def get_user_alerts(self, user_id, limit=50):
        """Get alerts for a specific user"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM alerts 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(user_id, limit))
        conn.close()
        
        return df
    
    def update_alert_performance(self, alert_id, price_field, price_value, return_field, return_value):
        """Update alert performance data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            UPDATE alerts 
            SET {price_field} = ?, {return_field} = ?
            WHERE id = ?
        ''', (price_value, return_value, alert_id))
        
        # Check if successful (>2% return in any timeframe)
        cursor.execute('''
            UPDATE alerts 
            SET is_successful = CASE 
                WHEN return_1h > 0.02 OR return_1d > 0.02 OR return_1w > 0.02 
                THEN 1 ELSE 0 END
            WHERE id = ?
        ''', (alert_id,))
        
        conn.commit()
        conn.close()
    
    def get_performance_stats(self, user_id):
        """Get performance statistics for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total alerts
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE user_id = ?', (user_id,))
        total_alerts = cursor.fetchone()[0]
        
        # Successful alerts
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE user_id = ? AND is_successful = 1', (user_id,))
        successful_alerts = cursor.fetchone()[0]
        
        # Average returns
        cursor.execute('''
            SELECT 
                AVG(return_1h) as avg_1h,
                AVG(return_1d) as avg_1d,
                AVG(return_1w) as avg_1w
            FROM alerts 
            WHERE user_id = ? AND return_1w IS NOT NULL
        ''', (user_id,))
        
        avg_returns = cursor.fetchone()
        conn.close()
        
        success_rate = (successful_alerts / total_alerts * 100) if total_alerts > 0 else 0
        
        return {
            'total_alerts': total_alerts,
            'successful_alerts': successful_alerts,
            'success_rate': success_rate,
            'avg_return_1h': avg_returns[0] if avg_returns[0] else 0,
            'avg_return_1d': avg_returns[1] if avg_returns[1] else 0,
            'avg_return_1w': avg_returns[2] if avg_returns[2] else 0
        }
    
    def add_to_watchlist(self, user_id, symbol):
        """Add stock to user's watchlist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO watchlist (user_id, symbol) VALUES (?, ?)', (user_id, symbol))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_watchlist(self, user_id):
        """Get user's watchlist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT symbol FROM watchlist WHERE user_id = ?', (user_id,))
        symbols = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return symbols