import mysql.connector
import threading
import logging

class Database:
    def __init__(self, db_name='crypto_data', user=None, password=None, host='localhost', port=3306):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        if self.user and self.password:
            self.create_database()
            self.create_table()

    def create_database(self):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
            conn.commit()
            conn.close()
            logging.info("Database created.")

    def create_table(self):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crypto_prices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trading_pair VARCHAR(255) NOT NULL,
                    price DOUBLE NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rsi_values (
                    trading_pair VARCHAR(255) NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    rsi_value DOUBLE NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (trading_pair, `interval`)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sma_values (
                    trading_pair VARCHAR(255) NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    sma_value DOUBLE NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (trading_pair, `interval`)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bollinger_bands (
                    trading_pair VARCHAR(255) NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    bb_sma DOUBLE NOT NULL,
                    bb_upper DOUBLE NOT NULL,
                    bb_lower DOUBLE NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (trading_pair, `interval`)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stochastic_values (
                    trading_pair VARCHAR(255) NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    stochastic_value DOUBLE NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (trading_pair, `interval`)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS macd_values (
                    trading_pair VARCHAR(255) NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    macd_line DOUBLE NOT NULL,
                    signal_line DOUBLE NOT NULL,
                    macd_histogram DOUBLE NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (trading_pair, `interval`)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fibonacci_levels (
                    trading_pair VARCHAR(255) NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    fib_23_6 DOUBLE NOT NULL,
                    fib_38_2 DOUBLE NOT NULL,
                    fib_50_0 DOUBLE NOT NULL,
                    fib_61_8 DOUBLE NOT NULL,
                    fib_78_6 DOUBLE NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (trading_pair, `interval`)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weighted_scores (
                    trading_pair VARCHAR(255) NOT NULL,
                    `interval` VARCHAR(255) NOT NULL,
                    score INT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (trading_pair, `interval`)
                )
            ''')
            conn.commit()
            conn.close()
            logging.info("Database tables created.")

    def insert_price(self, trading_pair, price, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crypto_prices (trading_pair, price, `interval`)
                VALUES (%s, %s, %s)
            ''', (trading_pair, price, interval))
            conn.commit()
            conn.close()
            logging.info(f"Inserted price for {trading_pair} with interval {interval}: {price}")
    
    def update_rsi(self, trading_pair, rsi_value, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rsi_values (trading_pair, rsi_value, `interval`)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                rsi_value=VALUES(rsi_value),
                timestamp=CURRENT_TIMESTAMP
            ''', (trading_pair, rsi_value, interval))
            conn.commit()
            conn.close()
            logging.info(f"Updated RSI for {trading_pair} with interval {interval}: {rsi_value}")
    
    def update_sma(self, trading_pair, sma_value, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sma_values (trading_pair, sma_value, `interval`)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                sma_value=VALUES(sma_value),
                timestamp=CURRENT_TIMESTAMP
            ''', (trading_pair, sma_value, interval))
            conn.commit()
            conn.close()
            logging.info(f"Updated SMA for {trading_pair} with interval {interval}: {sma_value}")

    def update_bollinger_bands(self, trading_pair, bb_sma, bb_upper, bb_lower, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bollinger_bands (trading_pair, bb_sma, bb_upper, bb_lower, `interval`)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                bb_sma=VALUES(bb_sma),
                bb_upper=VALUES(bb_upper),
                bb_lower=VALUES(bb_lower),
                timestamp=CURRENT_TIMESTAMP
            ''', (trading_pair, bb_sma, bb_upper, bb_lower, interval))
            conn.commit()
            conn.close()
            logging.info(f"Updated Bollinger Bands for {trading_pair} with interval {interval}: SMA={bb_sma}, Upper={bb_upper}, Lower={bb_lower}")

    def update_stochastic(self, trading_pair, stochastic_value, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO stochastic_values (trading_pair, stochastic_value, `interval`)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                stochastic_value=VALUES(stochastic_value),
                timestamp=CURRENT_TIMESTAMP
            ''', (trading_pair, stochastic_value, interval))
            conn.commit()
            conn.close()
            logging.info(f"Updated Stochastic Oscillator for {trading_pair} with interval {interval}: {stochastic_value}")

    def update_macd(self, trading_pair, macd_line, signal_line, macd_histogram, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO macd_values (trading_pair, macd_line, signal_line, macd_histogram, `interval`)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                macd_line=VALUES(macd_line),
                signal_line=VALUES(signal_line),
                macd_histogram=VALUES(macd_histogram),
                timestamp=CURRENT_TIMESTAMP
            ''', (trading_pair, macd_line, signal_line, macd_histogram, interval))
            conn.commit()
            conn.close()
            logging.info(f"Updated MACD for {trading_pair} with interval {interval}: MACD Line={macd_line}, Signal Line={signal_line}, Histogram={macd_histogram}")

    def update_fibonacci(self, trading_pair, fib_levels, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO fibonacci_levels (trading_pair, fib_23_6, fib_38_2, fib_50_0, fib_61_8, fib_78_6, `interval`)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                fib_23_6=VALUES(fib_23_6),
                fib_38_2=VALUES(fib_38_2),
                fib_50_0=VALUES(fib_50_0),
                fib_61_8=VALUES(fib_61_8),
                fib_78_6=VALUES(fib_78_6),
                timestamp=CURRENT_TIMESTAMP
            ''', (trading_pair, fib_levels["23.6%"], fib_levels["38.2%"], fib_levels["50.0%"], fib_levels["61.8%"], fib_levels["78.6%"], interval))
            conn.commit()
            conn.close()
            logging.info(f"Updated Fibonacci levels for {trading_pair} with interval {interval}: {fib_levels}")

    def update_weighted_score(self, trading_pair, score, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO weighted_scores (trading_pair, score, `interval`)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                score=VALUES(score),
                timestamp=CURRENT_TIMESTAMP
            ''', (trading_pair, score, interval))
            conn.commit()
            conn.close()
            logging.info(f"Updated weighted score for {trading_pair} with interval {interval}: {score}")

    def fetch_prices(self, trading_pair, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM crypto_prices WHERE trading_pair = %s AND `interval` = %s
                ORDER BY timestamp DESC
            ''', (trading_pair, interval))
            rows = cursor.fetchall()
            conn.close()
            logging.info(f"Fetched prices for {trading_pair} with interval {interval}: {rows}")
            return rows

    def fetch_rsi(self, trading_pair, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM rsi_values WHERE trading_pair = %s AND `interval` = %s
            ''', (trading_pair, interval))
            row = cursor.fetchone()
            conn.close()
            logging.info(f"Fetched RSI for {trading_pair} with interval {interval}: {row}")
            return row

    def fetch_sma(self, trading_pair, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sma_values WHERE trading_pair = %s AND `interval` = %s
            ''', (trading_pair, interval))
            row = cursor.fetchone()
            conn.close()
            logging.info(f"Fetched SMA for {trading_pair} with interval {interval}: {row}")
            return row

    def fetch_bollinger_bands(self, trading_pair, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM bollinger_bands WHERE trading_pair = %s AND `interval` = %s
            ''', (trading_pair, interval))
            row = cursor.fetchone()
            conn.close()
            logging.info(f"Fetched Bollinger Bands for {trading_pair} with interval {interval}: {row}")
            return row

    def fetch_stochastic(self, trading_pair, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM stochastic_values WHERE trading_pair = %s AND `interval` = %s
            ''', (trading_pair, interval))
            row = cursor.fetchone()
            conn.close()
            logging.info(f"Fetched Stochastic Oscillator for {trading_pair} with interval {interval}: {row}")
            return row

    def fetch_macd(self, trading_pair, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM macd_values WHERE trading_pair = %s AND `interval` = %s
            ''', (trading_pair, interval))
            row = cursor.fetchone()
            conn.close()
            logging.info(f"Fetched MACD for {trading_pair} with interval {interval}: {row}")
            return row

    def fetch_fibonacci_levels(self, trading_pair, interval):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM fibonacci_levels WHERE trading_pair = %s AND `interval` = %s
            ''', (trading_pair, interval))
            row = cursor.fetchone()
            conn.close()
            logging.info(f"Fetched Fibonacci Levels for {trading_pair} with interval {interval}: {row}")
            return row

    def delete_oldest_price(self, trading_pair):
        with self.lock:
            conn = mysql.connector.connect(user=self.user, password=self.password, host=self.host, port=self.port, database=self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM crypto_prices WHERE id = (
                    SELECT id FROM crypto_prices WHERE trading_pair = %s
                    ORDER BY timestamp ASC LIMIT 1
                )
            ''', (trading_pair,))
            conn.commit()
            conn.close()
            logging.info(f"Deleted oldest price for {trading_pair}")