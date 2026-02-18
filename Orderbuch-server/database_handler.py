# database_handler.py
import mysql.connector
import random 
from datetime import datetime, timedelta
import threading
import json
import time
import os 

class DatabaseHandler:
    def __init__(self, logger, db_config):
        self.logger = logger
        self.db_config = db_config
        self.lock = threading.Lock()
        self.conn = None
        self.logger.info(f"Initializing DatabaseHandler with database at: {self.db_config}")
        self.setup_database()
        self.logger.info("DatabaseHandler initialization complete")

    def get_connection(self):
        """Get a persistent database connection"""
        try:
            if self.conn is None or not self.conn.is_connected():
                self.logger.debug("Attempting to connect to the database...")
                self.conn = mysql.connector.connect(**self.db_config)
                self.logger.debug("Database connection established.")
            return self.conn
        except mysql.connector.Error as e:
            self.logger.error(f"Error connecting to the database: {str(e)}")
            raise

    def close(self):
        """Close database connection"""
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                self.conn = None
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {str(e)}")
    
    def setup_database(self):
        """Initialize database tables with proper indexes"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create orders table with all necessary fields
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id VARCHAR(255) PRIMARY KEY,
                    order_id VARCHAR(255) NOT NULL,
                    order_type VARCHAR(255) NOT NULL,
                    trading_pair VARCHAR(255) NOT NULL,
                    price DECIMAL(20,8),
                    amount DECIMAL(20,8),
                    min_amount DECIMAL(20,8),
                    volume DECIMAL(20,8),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    seat_of_bank VARCHAR(255),
                    min_trust_level VARCHAR(255),
                    trade_to_sepa_country VARCHAR(255),
                    is_kyc_full BOOLEAN,
                    payment_option INTEGER,
                    raw_data TEXT,
                    UNIQUE(id(255))
                )
            ''')
            
            # Create indexes for frequent queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trading_pair 
                ON orders(trading_pair)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_order_id 
                ON orders(order_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON orders(timestamp)
            ''')
            
            conn.commit()
            self.logger.info("Database setup completed successfully")
            
        except mysql.connector.Error as e:
            self.logger.error(f"Database setup error: {str(e)}")
            raise
    
    def _add_order(self, order):
        """Add or update order in database"""
        try:
            with self.lock:  # Make sure we're using thread-safe access
                conn = self.get_connection()
                cursor = conn.cursor()
                
                try:
                    # Extract relevant fields
                    order_data = {
                        'id': order.get('id'),
                        'order_id': order.get('order_id'),
                        'order_type': order.get('order_type'),
                        'trading_pair': order.get('trading_pair'),
                        'price': float(order.get('price', 0)),
                        'amount': float(order.get('amount', 0)),
                        'min_amount': float(order.get('min_amount', 0)),
                        'volume': float(order.get('volume', 0)),
                        'seat_of_bank': order.get('seat_of_bank_of_creator'),
                        'min_trust_level': order.get('min_trust_level'),
                        'trade_to_sepa_country': order.get('trade_to_sepa_country'),
                        'is_kyc_full': bool(int(order.get('is_kyc_full', 0))),
                        'payment_option': int(order.get('payment_option', 0)),
                        'raw_data': json.dumps(order)
                    }
                    
                    # Insert or replace order
                    cursor.execute('''
                        INSERT INTO orders 
                        (id, order_id, order_type, trading_pair, price, amount, 
                        min_amount, volume, seat_of_bank, min_trust_level, 
                        trade_to_sepa_country, is_kyc_full, payment_option, raw_data)
                        VALUES 
                        (%(id)s, %(order_id)s, %(order_type)s, %(trading_pair)s, %(price)s, %(amount)s,
                        %(min_amount)s, %(volume)s, %(seat_of_bank)s, %(min_trust_level)s,
                        %(trade_to_sepa_country)s, %(is_kyc_full)s, %(payment_option)s, %(raw_data)s)
                        ON DUPLICATE KEY UPDATE
                        order_id=VALUES(order_id), order_type=VALUES(order_type), trading_pair=VALUES(trading_pair),
                        price=VALUES(price), amount=VALUES(amount), min_amount=VALUES(min_amount), volume=VALUES(volume),
                        seat_of_bank=VALUES(seat_of_bank), min_trust_level=VALUES(min_trust_level), trade_to_sepa_country=VALUES(trade_to_sepa_country),
                        is_kyc_full=VALUES(is_kyc_full), payment_option=VALUES(payment_option), raw_data=VALUES(raw_data)
                    ''', order_data)
                    
                    conn.commit()
                    self.logger.info(f"Successfully added/updated order: {order_data['order_id']}")
                    
                    # Log database stats periodically
                    if random.random() < 0.1:  # Only log ~10% of the time to avoid spam
                        cursor.execute("SELECT COUNT(*) FROM orders")
                        count = cursor.fetchone()[0]
                        self.logger.info(f"Current orders in database: {count}")
                    
                except mysql.connector.Error as e:
                    conn.rollback()
                    self.logger.error(f"Transaction failed, rolling back: {str(e)}")
                    raise
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Unexpected error during transaction, rolling back: {str(e)}")
                    raise
                    
        except mysql.connector.Error as e:
            self.logger.error(f"MySQL error adding order {order.get('order_id', 'unknown')}: {str(e)}")
            self.logger.exception("Full MySQL error traceback:")
        except Exception as e:
            self.logger.error(f"Unexpected error adding order {order.get('order_id', 'unknown')}: {str(e)}")
            self.logger.exception("Full error traceback:")

    def _remove_order(self, order):
        """Remove order from database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                try:
                    # Log the current state
                    cursor.execute("SELECT order_id FROM orders WHERE order_id = %s", 
                                 (order.get('order_id'),))
                    if cursor.fetchone():
                        self.logger.info(f"Found order {order.get('order_id')} to remove")
                    else:
                        self.logger.warning(f"Order {order.get('order_id')} not found in database")
                    
                    # Perform the delete
                    cursor.execute('''
                        DELETE FROM orders 
                        WHERE order_id = %s OR id = %s
                    ''', (order.get('order_id'), order.get('id')))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    self.logger.info(f"Removed {deleted_count} orders with ID {order.get('order_id')}")
                    
                except Exception as e:
                    conn.rollback()
                    self.logger.error(f"Transaction failed, rolling back: {str(e)}")
                    raise
                    
        except mysql.connector.Error as e:
            self.logger.error(f"MySQL error removing order: {str(e)}")
            self.logger.exception("Full MySQL error traceback:")
        except Exception as e:
            self.logger.error(f"Unexpected error removing order: {str(e)}")
            self.logger.exception("Full error traceback:")       
          
    def process_order(self, action, order):
        """Process an order (add or remove)"""
        try:
            if not order:
                self.logger.error("Received empty order")
                return
    
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
            
                if action == 'add':
                    # Insert or update order
                    cursor.execute('''
                        INSERT INTO orders (
                            id,
                            order_id,
                            order_type,
                            trading_pair,
                            price,
                            amount,
                            min_amount,
                            volume,
                            seat_of_bank,
                            min_trust_level,
                            trade_to_sepa_country,
                            is_kyc_full,
                            payment_option,
                            raw_data
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        order_id=VALUES(order_id), order_type=VALUES(order_type), trading_pair=VALUES(trading_pair),
                        price=VALUES(price), amount=VALUES(amount), min_amount=VALUES(min_amount), volume=VALUES(volume),
                        seat_of_bank=VALUES(seat_of_bank), min_trust_level=VALUES(min_trust_level), trade_to_sepa_country=VALUES(trade_to_sepa_country),
                        is_kyc_full=VALUES(is_kyc_full), payment_option=VALUES(payment_option), raw_data=VALUES(raw_data)
                    ''', (
                        order.get('id'),
                        order.get('order_id'),
                        order.get('order_type'),
                        order.get('trading_pair'),
                        order.get('price'),
                        order.get('amount'),
                        order.get('min_amount'),
                        order.get('volume'),
                        order.get('seat_of_bank'),
                        order.get('min_trust_level'),
                        order.get('trade_to_sepa_country'),
                        order.get('is_kyc_full'),
                        order.get('payment_option'),
                        str(order)  # Store complete order as string in raw_data
                    ))
                    self.logger.info(f"Added/Updated order: {order.get('order_id')} for {order.get('trading_pair')}")
            
                elif action == 'remove':
                    # Remove order
                    cursor.execute('''
                        DELETE FROM orders 
                        WHERE order_id = %s
                    ''', (order.get('order_id'),))
                    self.logger.info(f"Removed order: {order.get('order_id')}")
            
                conn.commit()
                cursor.close()
    
        except Exception as e:
            self.logger.error(f"Error processing order: {str(e)}")
            self.logger.error(f"Order data: {order}")
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute('SELECT COUNT(*) FROM orders')
                total_count = cursor.fetchone()[0]
                
                # Get count by trading pair
                cursor.execute('''
                    SELECT trading_pair, COUNT(*) 
                    FROM orders 
                    GROUP BY trading_pair
                ''')
                pair_counts = cursor.fetchall()
                
                # Get database file size
                db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # Size in MB
                
                self.logger.info(f"Database Stats:")
                self.logger.info(f"Total orders: {total_count}")
                self.logger.info(f"Database size: {db_size:.2f} MB")
                for pair, count in pair_counts:
                    self.logger.info(f"Orders for {pair}: {count}")
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")

    def view_recent_orders(self, limit=10):
        """View most recent orders"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT order_id, trading_pair, order_type, price, amount, timestamp
                    FROM orders
                    ORDER BY timestamp DESC
                    LIMIT %s
                ''', (limit,))
            
                orders = cursor.fetchall()
                for order in orders:
                    self.logger.info(f"Order: {order}")
            
                return orders
            
        except Exception as e:
            self.logger.error(f"Error viewing orders: {str(e)}")
            return []

    def cleanup_old_data(self):
        """Remove orders older than 2 days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM orders WHERE timestamp < %s', (cutoff_date,))
                conn.commit()
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old orders")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def get_orders_count(self):
        """Get total number of orders in database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM orders")
                count = cursor.fetchone()[0]
                self.logger.debug(f"Total orders count: {count}")
                cursor.close()
                return count
        except Exception as e:
            self.logger.error(f"Error getting orders count: {str(e)}")
            return 0

    def get_orders_count_by_pair(self, trading_pair):
        """Get number of orders for specific trading pair"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM orders 
                    WHERE trading_pair = %s
                ''', (trading_pair,))
                count = cursor.fetchone()[0]
                self.logger.debug(f"Orders count for {trading_pair}: {count}")
                cursor.close()
                return count
        except Exception as e:
            self.logger.error(f"Error getting orders count for {trading_pair}: {str(e)}")
            return 0

    def get_trading_pairs(self):
        """Get list of all trading pairs in database"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT DISTINCT trading_pair 
                        FROM orders 
                        ORDER BY trading_pair
                    ''')
                    pairs = [row[0] for row in cursor.fetchall()]
                    self.logger.debug(f"Found trading pairs: {pairs}")
                    return pairs
        except Exception as e:
            self.logger.error(f"Error getting trading pairs: {str(e)}")
            return []

    def get_database_stats(self):
        """Get comprehensive database statistics"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get total count
                    cursor.execute("SELECT COUNT(*) FROM orders")
                    total_count = cursor.fetchone()[0]
                    
                    # Get count by trading pair
                    cursor.execute('''
                        SELECT trading_pair, COUNT(*) 
                        FROM orders 
                        GROUP BY trading_pair
                    ''')
                    pair_counts = dict(cursor.fetchall())
                    
                    # Get count by order type
                    cursor.execute('''
                        SELECT order_type, COUNT(*) 
                        FROM orders 
                        GROUP BY order_type
                    ''')
                    type_counts = dict(cursor.fetchall())
                    
                    stats = {
                        'total_orders': total_count,
                        'by_pair': pair_counts,
                        'by_type': type_counts
                    }
                    
                    if self.logging_enabled:
                        self.logger.debug(f"Database stats: {stats}")
                    return stats
                    
        except mysql.connector.Error as e:
            self.logger.error(f"MySQL error getting database stats: {str(e)}")
            return {'total_orders': 0, 'by_pair': {}, 'by_type': {}}
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {'total_orders': 0, 'by_pair': {}, 'by_type': {}}

    def debug_database_status(self):
        """Print database status for debugging"""
        try:
            with self.lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get total count
                    cursor.execute("SELECT COUNT(*) FROM orders")
                    total_count = cursor.fetchone()[0]
                    self.logger.info(f"Total orders in database: {total_count}")
                    
                    # Get counts by trading pair
                    cursor.execute('''
                        SELECT trading_pair, COUNT(*) 
                        FROM orders 
                        GROUP BY trading_pair
                    ''')
                    pair_counts = cursor.fetchall()
                    for pair, count in pair_counts:
                        self.logger.info(f"Trading pair {pair}: {count} orders")
                    
                    # Get sample of orders
                    cursor.execute('''
                        SELECT order_id, trading_pair, price, amount 
                        FROM orders 
                        LIMIT 5
                    ''')
                    sample_orders = cursor.fetchall()
                    if sample_orders:
                        self.logger.info("Sample orders:")
                        for order in sample_orders:
                            self.logger.info(f"Order {order[0]}: {order[1]} - Price: {order[2]}, Amount: {order[3]}")
                    else:
                        self.logger.info("No orders found in database")
                        
        except Exception as e:
            self.logger.error(f"Error checking database status: {str(e)}")

    def setup_cleanup_task(self):
        """Setup periodic cleanup task"""
        def cleanup_task():
            while True:
                self.cleanup_old_data()
                self.get_database_stats()
                time.sleep(3600)  # Run every hour

        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
