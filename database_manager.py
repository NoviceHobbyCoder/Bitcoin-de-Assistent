from threading import Lock
import logging
import mariadb
 
class DatabaseManager:
    def __init__(self, db_config: dict, logger):
        self.db_config = db_config
        self.logger = logger
        self.lock = Lock()
        self.init_database()
        
    def get_connection(self):
        """Get a new database connection"""
        try:
            return mariadb.connect(**self.db_config)
        except mariadb.Error as e:
            self.logger.error(f"Error connecting to the database: {str(e)}")
            raise

    def init_database(self):
        """Initialize the database with required schema"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Create orders table if it does not exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        trading_pair VARCHAR(255) NOT NULL,
                        price DECIMAL(20,8) NOT NULL,
                        amount DECIMAL(20,8) NOT NULL,
                        min_amount DECIMAL(20,8),
                        order_id VARCHAR(255) NOT NULL,
                        order_type ENUM('buy', 'sell') NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (trading_pair, price, amount, order_type, timestamp)
                    )
                """)
                
                # Check if the column 'min_amount' exists, and add it if it doesn't
                cursor.execute("SHOW COLUMNS FROM orders LIKE 'min_amount'")
                result = cursor.fetchone()
                if not result:
                    cursor.execute("ALTER TABLE orders ADD COLUMN min_amount DECIMAL(20,8)")
                    self.logger.info("Added 'min_amount' column to 'orders' table")
                
                # Check if the column 'order_id' exists, and add it if it doesn't
                cursor.execute("SHOW COLUMNS FROM orders LIKE 'order_id'")
                result = cursor.fetchone()
                if not result:
                    cursor.execute("ALTER TABLE orders ADD COLUMN order_id VARCHAR(255) NOT NULL")
                    self.logger.info("Added 'order_id' column to 'orders' table")
                
                # Create analysis_data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_data (
                        trading_pair VARCHAR(255) NOT NULL,
                        `interval` VARCHAR(255) NOT NULL,
                        rsi_value DOUBLE NOT NULL,
                        bb_sma DOUBLE NOT NULL,
                        stochastic_value DOUBLE NOT NULL,
                        score DOUBLE NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (trading_pair, `interval`)
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_orders_pair_time 
                    ON orders(trading_pair, timestamp)
                """)
                
                conn.commit()
                cursor.close()
                conn.close()
                self.logger.info("Database schema initialized successfully")
                
        except mariadb.Error as e:
            self.logger.error(f"Failed to initialize database schema: {str(e)}")
            raise

    def get_orderbook(self, trading_pair: str) -> dict:
        """Get current orderbook data for the specified trading pair"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Get all active orders for the trading pair
                cursor.execute("""
                    SELECT order_type, price, amount, min_amount, timestamp, order_id
                    FROM orders 
                    WHERE trading_pair = ?
                """, (trading_pair,))
                
                rows = cursor.fetchall()
                
                asks = []  # sell orders
                bids = []  # buy orders
                
                for order_type, price, amount, min_amount, timestamp, order_id in rows:
                    if order_type and price and amount:  # Ensure we have valid data
                        order_data = [str(price), str(amount), str(min_amount), order_id]
                        if order_type.lower() == 'sell':
                            asks.append(order_data)
                        elif order_type.lower() == 'buy':
                            bids.append(order_data)
                
                # Sort the orders after collecting them
                asks.sort(key=lambda x: float(x[0]))  # Sort asks by price ascending
                bids.sort(key=lambda x: float(x[0]), reverse=True)  # Sort bids by price descending
                
                cursor.close()
                conn.close()
                
                return {'orders': {'asks': asks, 'bids': bids}}
                
        except mariadb.Error as e:
            self.logger.error(f"Database error: {str(e)}")
            return {'orders': {'asks': [], 'bids': []}}
        except Exception as e:
            self.logger.error(f"Error fetching orderbook data: {str(e)}")
            return {'orders': {'asks': [], 'bids': []}}

    def check_orders(self, trading_pair: str):
        """Check orders in database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT order_type, price, amount, timestamp
                    FROM orders 
                    WHERE trading_pair = ?
                    ORDER BY timestamp DESC
                """, (trading_pair,))
                
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return len(rows)
        except Exception as e:
            self.logger.error(f"Error checking orders: {str(e)}")
            return 0

    def get_analysis_data(self, trading_pair: str, interval: str) -> dict:
        """Get analysis data for the specified trading pair and interval"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Fetch RSI value
                cursor.execute("""
                    SELECT rsi_value
                    FROM rsi_values
                    WHERE trading_pair = ? AND `interval` = ?
                """, (trading_pair, interval))
                rsi_row = cursor.fetchone()
                rsi_value = rsi_row[0] if rsi_row else None

                # Fetch BB SMA value
                cursor.execute("""
                    SELECT bb_sma
                    FROM bollinger_bands
                    WHERE trading_pair = ? AND `interval` = ?
                """, (trading_pair, interval))
                bb_sma_row = cursor.fetchone()
                bb_sma_value = bb_sma_row[0] if bb_sma_row else None

                # Fetch Stochastic value
                cursor.execute("""
                    SELECT stochastic_value
                    FROM stochastic_values
                    WHERE trading_pair = ? AND `interval` = ?
                """, (trading_pair, interval))
                stochastic_row = cursor.fetchone()
                stochastic_value = stochastic_row[0] if stochastic_row else None

                # Fetch Score value
                cursor.execute("""
                    SELECT score
                    FROM weighted_scores
                    WHERE trading_pair = ? AND `interval` = ?
                """, (trading_pair, interval))
                score_row = cursor.fetchone()
                score_value = score_row[0] if score_row else None

                cursor.close()
                conn.close()
                
                return {
                    'rsi_value': rsi_value,
                    'bb_sma': bb_sma_value,
                    'stochastic_value': stochastic_value,
                    'score': score_value
                }
                
        except mariadb.Error as e:
            self.logger.error(f"Database error: {str(e)}")
            return {}
        except Exception as e:
            self.logger.error(f"Error fetching analysis data: {str(e)}")
            return {}
       