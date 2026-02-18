from threading import Lock
import logging
import sqlite3
import os
from tkinter import messagebox
from constants import Currency
from pathlib import Path

class SQLiteDatabaseManager:
    def __init__(self, sqlite_db_path: str = None, logger=None):
        if sqlite_db_path is None:
            #base_dir = Path(os.path.expanduser('~/.bitcoin_assistent')) # Use the User's home directory 
            base_dir = Path(os.path.dirname(os.path.abspath(__file__)))  # Use the program directory
            base_dir.mkdir(parents=True, exist_ok=True)
            sqlite_db_path = base_dir / 'database.db'
        
        self.sqlite_db_path = os.path.abspath(sqlite_db_path)  # Ensure the path is absolute
        self.logger = logger or logging.getLogger(__name__)
        self.lock = Lock()
        self.init_sqlite_database()

    def get_sqlite_connection(self):
        """Get a new SQLite database connection"""
        try:
            return sqlite3.connect(self.sqlite_db_path)
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to the SQLite database: {str(e)}")
            raise

    def init_sqlite_database(self):
        """Initialize the SQLite database with required schema"""
        try:
            with self.lock:
                conn = self.get_sqlite_connection()
                cursor = conn.cursor()
                
                # Create ledger table if it does not exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ledger (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        currency TEXT NOT NULL,
                        entry_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        type TEXT,
                        trade_id TEXT,
                        price REAL,
                        is_external_wallet_trade BOOLEAN,
                        trading_pair TEXT,
                        currency_to_trade TEXT,
                        before_fee_trade REAL,
                        after_fee_trade REAL,
                        currency_to_pay TEXT,
                        before_fee_pay REAL,
                        after_fee_pay REAL,
                        balance REAL,
                        UNIQUE (entry_id, amount, timestamp, type)  -- Composite unique key
                    )
                """)
                conn.commit()
                cursor.close()
                conn.close()
        except sqlite3.Error as e:
            self.logger.error(f"Error initializing the SQLite database: {str(e)}")
            raise

    def save_ledger_data(self, currency, data):
        """Save ledger data to the SQLite database"""
        try:
            with self.lock:
                conn = self.get_sqlite_connection()
                cursor = conn.cursor()
                for entry in data.get('account_ledger', []):
                    try:
                        # Extract relevant fields from the entry, using default values if necessary
                        entry_id = entry.get('reference') if entry.get('reference') else 'N/A'
                        amount = float(entry.get('cashflow', 0))
                        timestamp = entry.get('date', '1970-01-01T00:00:00+00:00')
                        type = entry.get('type', 'N/A')
                        trade_id = entry.get('trade', {}).get('trade_id', 'N/A')
                        price = float(entry.get('trade', {}).get('price', 0))
                        is_external_wallet_trade = entry.get('trade', {}).get('is_external_wallet_trade', False)
                        trading_pair = entry.get('trade', {}).get('trading_pair', 'N/A')
                        currency_to_trade = entry.get('trade', {}).get('currency_to_trade', {}).get('currency', 'N/A')
                        before_fee_trade = float(entry.get('trade', {}).get('currency_to_trade', {}).get('before_fee', 0))
                        after_fee_trade = float(entry.get('trade', {}).get('currency_to_trade', {}).get('after_fee', 0))
                        currency_to_pay = entry.get('trade', {}).get('currency_to_pay', {}).get('currency', 'N/A')
                        before_fee_pay = float(entry.get('trade', {}).get('currency_to_pay', {}).get('before_fee', 0))
                        after_fee_pay = float(entry.get('trade', {}).get('currency_to_pay', {}).get('after_fee', 0))
                        balance = float(entry.get('balance', 0))

                        # Insert the entry into the database
                        cursor.execute("""
                            INSERT INTO ledger (
                                currency, entry_id, amount, timestamp, type, trade_id, price, 
                                is_external_wallet_trade, trading_pair, currency_to_trade, before_fee_trade, 
                                after_fee_trade, currency_to_pay, before_fee_pay, after_fee_pay, balance
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            currency, entry_id, amount, timestamp, type, trade_id, price, 
                            is_external_wallet_trade, trading_pair, currency_to_trade, before_fee_trade, 
                            after_fee_trade, currency_to_pay, before_fee_pay, 
                            after_fee_pay, balance
                        ))
                    except sqlite3.IntegrityError:
                        self.logger.info(f"Entry {entry_id} with amount {amount} already exists, skipping.")
                conn.commit()
                cursor.close()
                conn.close()
        except sqlite3.Error as e:
            self.logger.error(f"Error saving ledger data: {str(e)}")
            raise