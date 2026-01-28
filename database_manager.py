# database_manager.py
# ---------------------------------------------------------
# SQLite Database Manager
# Implements WAL Mode for high concurrency and stability.
# ---------------------------------------------------------
import sqlite3
from datetime import datetime
from config import DB_NAME, TABLE_LOGS
from icecream import ic

class DatabaseManager:
    def __init__(self):
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Creates a connection and enables Write-Ahead Logging (WAL)."""
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.execute("PRAGMA journal_mode=WAL;") 
            return conn
        except sqlite3.Error as e:
            ic(f"DB Connection Error: {e}")
            return None

    def init_db(self) -> None:
        """Initializes the logs table schema."""
        sql_create_table = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_LOGS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                topic TEXT NOT NULL,
                message TEXT NOT NULL,
                event_type TEXT
            );
        """
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql_create_table)
                conn.commit()
                ic("Database initialized successfully (WAL Mode Enabled).")
            except sqlite3.Error as e:
                ic(f"Create Table Error: {e}")
            finally:
                conn.close()

    def insert_log(self, topic: str, message: str, event_type: str = "INFO") -> None:
        """Thread-safe logging insertion."""
        sql = f''' INSERT INTO {TABLE_LOGS}(timestamp, topic, message, event_type)
                   VALUES(?,?,?,?) '''
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql, (timestamp, topic, message, event_type))
                conn.commit()
            except sqlite3.Error as e:
                ic(f"Insert Error: {e}")
            finally:
                conn.close()