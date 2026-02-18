from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, END, ttk, StringVar
from cryptography.fernet import Fernet
import os
import json
import logging
from datetime import datetime
from api_client import ApiClient
from database import Database
from rsi_calculator import RsiCalculator
from sma_calculator import SmaCalculator
from bollinger_bands_calculator import BollingerBandsCalculator
from stochastic_oscillator_calculator import StochasticOscillatorCalculator
from macd_calculator import MacdCalculator
from fibonacci_calculator import FibonacciCalculator
import threading

class CryptoRsiGUI:
    def __init__(self, master, api_key, app):
        self.master = master
        self.api_key = api_key
        self.app = app
        master.title("Analyse Server")

        # Setzen des Icons
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        master.iconbitmap(icon_path)
    
        self.config_dir = os.path.join(os.path.expanduser("~"), ".Analyse Server")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.activation_file = os.path.join(self.config_dir, "db.config")
        self.key_file = os.path.join(self.config_dir, "key.key")
    
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if not os.path.exists(self.key_file):
            self.generate_key()
    
        self.header_frame = ttk.Frame(master)
        self.header_frame.pack(fill='x')

        self.title_label = Label(self.header_frame, text="Analyse Server", font=("Helvetica", 16))
        self.title_label.pack(side='left', padx=10)

        self.last_update_label = Label(self.header_frame, text="Last Update: N/A", font=("Helvetica", 10))
        self.last_update_label.pack(side='right', padx=10)

        self.tab_control = ttk.Notebook(master)
        self.tab_control.pack(expand=1, fill='both')

        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab1, text='RSI Data')
        self.tab_control.add(self.tab2, text='Settings')

        columns = ("Trading_Pair", "RSI", "SMA", "BB_SMA", "BB_Upper", "BB_Lower", "Stochastic", "MACD_Line", "Signal_Line", "MACD_Histogram", "Fib_Levels", "Score")
        self.tree = ttk.Treeview(self.tab1, columns=columns, show='headings')
        self.tree.pack(expand=1, fill='both')

        self.tree.heading("Trading_Pair", text="Trading Pair")
        self.tree.heading("RSI", text="RSI")
        self.tree.heading("SMA", text="SMA")
        self.tree.heading("BB_SMA", text="BB_SMA")
        self.tree.heading("BB_Upper", text="BB_Upper")
        self.tree.heading("BB_Lower", text="BB_Lower")
        self.tree.heading("Stochastic", text="Stochastic")
        self.tree.heading("MACD_Line", text="MACD_Line")
        self.tree.heading("Signal_Line", text="Signal_Line")
        self.tree.heading("MACD_Histogram", text="MACD_Histogram")
        self.tree.heading("Fib_Levels", text="Fib_Levels")
        self.tree.heading("Score", text="Score")

        # Set column widths
        self.tree.column("Trading_Pair", width=100)
        self.tree.column("RSI", width=50)
        self.tree.column("SMA", width=50)
        self.tree.column("BB_SMA", width=70)
        self.tree.column("BB_Upper", width=70)
        self.tree.column("BB_Lower", width=70)
        self.tree.column("Stochastic", width=80)
        self.tree.column("MACD_Line", width=80)
        self.tree.column("Signal_Line", width=80)
        self.tree.column("MACD_Histogram", width=100)
        self.tree.column("Fib_Levels", width=150)
        self.tree.column("Score", width=50)

        settings_frame = ttk.Frame(self.tab2)
        settings_frame.pack(fill='x', padx=10, pady=10)

        self.label = Label(settings_frame, text="API-Basic:")
        self.label.grid(row=0, column=0, sticky='e', padx=5, pady=5)

        self.api_key_entry = Entry(settings_frame)
        self.api_key_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        self.api_key_entry.insert(0, self.api_key)

        self.db_user_label = Label(settings_frame, text="DB User:")
        self.db_user_label.grid(row=1, column=0, sticky='e', padx=5, pady=5)

        self.db_user_entry = Entry(settings_frame)
        self.db_user_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        self.db_password_label = Label(settings_frame, text="DB Password:")
        self.db_password_label.grid(row=2, column=0, sticky='e', padx=5, pady=5)

        self.db_password_entry = Entry(settings_frame, show="*")
        self.db_password_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        self.db_host_label = Label(settings_frame, text="DB Host:")
        self.db_host_label.grid(row=0, column=2, sticky='e', padx=5, pady=5)

        self.db_host_entry = Entry(settings_frame)
        self.db_host_entry.grid(row=0, column=3, sticky='w', padx=5, pady=5)

        self.db_port_label = Label(settings_frame, text="DB Port:")
        self.db_port_label.grid(row=1, column=2, sticky='e', padx=5, pady=5)

        self.db_port_entry = Entry(settings_frame)
        self.db_port_entry.grid(row=1, column=3, sticky='w', padx=5, pady=5)

        self.db_name_label = Label(settings_frame, text="DB Name:")
        self.db_name_label.grid(row=2, column=2, sticky='e', padx=5, pady=5)

        self.db_name_entry = Entry(settings_frame)
        self.db_name_entry.grid(row=2, column=3, sticky='w', padx=5, pady=5)

        self.interval_label = Label(settings_frame, text="Intervall:")
        self.interval_label.grid(row=3, column=0, sticky='e', padx=5, pady=5)

        self.interval_var = StringVar(value='1 Stunde')
        self.interval_combobox = ttk.Combobox(
            settings_frame,
            textvariable=self.interval_var,
            values=['30 Minuten', '1 Stunde', '8 Stunden', '24 Stunden'],
            state='readonly'
        )
        self.interval_combobox.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        self.save_button = Button(settings_frame, text="Save Settings", command=self.save_settings)
        self.save_button.grid(row=4, column=0, columnspan=2, pady=10)

        self.fetch_button = Button(settings_frame, text="Fetch Data", command=self.fetch_data)
        self.fetch_button.grid(row=4, column=2, columnspan=2, pady=10)

        self.console_frame = ttk.Frame(self.tab2)
        self.console_frame.pack(expand=1, fill='both')

        self.console_text = Text(self.console_frame, wrap='word', height=10)
        self.console_text.pack(side='left', expand=1, fill='both')

        self.scrollbar_console = Scrollbar(self.console_frame, command=self.console_text.yview)
        self.scrollbar_console.pack(side='right', fill='y')
        self.console_text['yscrollcommand'] = self.scrollbar_console.set

        # Redirect logging to the console_text widget
        text_handler = TextHandler(self.console_text)
        text_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(text_handler)

        self.load_settings()

    def generate_key(self):
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as key_file:
            key_file.write(key)
    
    def load_key(self):
        return open(self.key_file, 'rb').read()
    
    def encrypt_data(self, data):
        key = self.load_key()
        fernet = Fernet(key)
        return fernet.encrypt(data.encode())
    
    def decrypt_data(self, data):
        key = self.load_key()
        fernet = Fernet(key)
        return fernet.decrypt(data).decode()

    def save_settings(self):
        settings = {
            'api_key': self.api_key_entry.get(),
            'db_user': self.db_user_entry.get(),
            'db_password': self.db_password_entry.get(),
            'db_host': self.db_host_entry.get(),
            'db_port': self.db_port_entry.get(),
            'db_name': self.db_name_entry.get(),
            'interval': self.interval_var.get()
        }
        encrypted_data = self.encrypt_data(json.dumps(settings))
        with open(self.config_file, 'wb') as config_file:
            config_file.write(encrypted_data)
        logging.info("Settings saved.")

    def load_settings(self):
        if not os.path.exists(self.config_file):
            logging.warning("No settings file found.")
            return
    
        try:
            with open(self.config_file, 'rb') as config_file:
                encrypted_data = config_file.read()
                decrypted_data = self.decrypt_data(encrypted_data)
                settings = json.loads(decrypted_data)
                self.api_key_entry.delete(0, END)  # Clear the entry before inserting
                self.api_key_entry.insert(0, settings.get('api_key', ''))
                self.db_user_entry.delete(0, END)
                self.db_user_entry.insert(0, settings.get('db_user', ''))
                self.db_password_entry.delete(0, END)
                self.db_password_entry.insert(0, settings.get('db_password', ''))
                self.db_host_entry.delete(0, END)
                self.db_host_entry.insert(0, settings.get('db_host', ''))
                self.db_port_entry.delete(0, END)
                self.db_port_entry.insert(0, settings.get('db_port', ''))
                self.db_name_entry.delete(0, END)
                self.db_name_entry.insert(0, settings.get('db_name', ''))
                self.interval_var.set(settings.get('interval', '1 Stunde'))
        except FileNotFoundError:
            logging.warning("No settings file found.")
        except Exception as e:
            logging.error(f"Fehler beim Laden der Einstellungen: {e}")

    def fetch_data(self):
        self.tree.delete(*self.tree.get_children())
    
        # Lesen Sie den API-Schlüssel direkt vor der Anfrage
        api_key = self.api_key_entry.get()
        self.api_client = ApiClient(api_key)
        
        try:
            self.database = Database(
                db_name=self.db_name_entry.get(),
                user=self.db_user_entry.get(),
                password=self.db_password_entry.get(),
                host=self.db_host_entry.get(),
                port=int(self.db_port_entry.get())
            )
        except Exception as e:
            logging.error(f"Fehler bei der Verbindung zur Datenbank: {e}")
            self.database = None
    
        self.rsi_calculator = RsiCalculator()
        self.sma_calculator = SmaCalculator()
        self.bollinger_bands_calculator = BollingerBandsCalculator()
        self.stochastic_oscillator_calculator = StochasticOscillatorCalculator()
        self.macd_calculator = MacdCalculator()
        self.fibonacci_calculator = FibonacciCalculator()
    
        def fetch_and_store():
            trading_pairs = ["btceur", "bcheur", "etheur", "soleur", "xrpeur", "ltceur", "dogeeur", "btgeur", "trxeur", "usdceur"]
            interval_mapping = {
                '30 Minuten': '30m',
                '1 Stunde': '1h',
                '8 Stunden': '8h',
                '24 Stunden': '24h'
            }
            interval_display = self.interval_var.get()
            interval = interval_mapping[interval_display]  # Map to the actual interval value
            for pair in trading_pairs:
                try:
                    rates = self.api_client.get_basic_rates(pair)
                    if rates and 'rate' in rates:
                        rate_weighted = float(rates['rate']['rate_weighted'])
                        if self.database:
                            try:
                                self.database.insert_price(pair, rate_weighted, interval)
                                prices = self.database.fetch_prices(pair, interval)
                                if len(prices) > 160:  # Limit the number of stored prices to 160
                                    self.database.delete_oldest_price(pair)
                                if len(prices) >= self.macd_calculator.long_period + self.macd_calculator.signal_period:
                                    price_values = [float(price[2]) for price in prices[-(self.macd_calculator.long_period + self.macd_calculator.signal_period):]]
                                    rsi_value = self.rsi_calculator.calculate_rsi(price_values)
                                    sma_value = self.sma_calculator.calculate_sma(price_values)
                                    bb_sma, bb_upper, bb_lower = self.bollinger_bands_calculator.calculate_bollinger_bands(price_values)
                                    stochastic_value = self.stochastic_oscillator_calculator.calculate_stochastic_oscillator(price_values)
                                    macd_line, signal_line, macd_histogram = self.macd_calculator.calculate_macd(price_values)
                                    fib_levels = self.fibonacci_calculator.calculate_fibonacci(price_values)
                                    if rsi_value is not None:
                                        self.database.update_rsi(pair, float(rsi_value), interval)
                                    if sma_value is not None:
                                        self.database.update_sma(pair, float(sma_value), interval)
                                    if bb_sma is not None and bb_upper is not None and bb_lower is not None:
                                        self.database.update_bollinger_bands(pair, float(bb_sma), float(bb_upper), float(bb_lower), interval)
                                    if stochastic_value is not None:
                                        self.database.update_stochastic(pair, float(stochastic_value), interval)
                                    if macd_line is not None and signal_line is not None and macd_histogram is not None:
                                        self.database.update_macd(pair, float(macd_line), float(signal_line), float(macd_histogram), interval)
                                    if fib_levels is not None:
                                        self.database.update_fibonacci(pair, {key: float(value) for key, value in fib_levels.items()}, interval)
                                    if all(value is not None for value in [rsi_value, macd_line, signal_line, bb_sma, bb_upper, bb_lower, stochastic_value, fib_levels]):
                                        current_price = price_values[-1]  # Extrahiere den aktuellen Preis
                                        score = self.app.calculate_weighted_score(current_price, rsi_value, macd_line, signal_line, bb_sma, bb_upper, bb_lower, stochastic_value, fib_levels)
                                        self.database.update_weighted_score(pair, float(score), interval)
                                        self.update_rsi(pair, float(rsi_value), float(sma_value), float(bb_sma), float(bb_upper), float(bb_lower), float(stochastic_value), float(macd_line), float(signal_line), float(macd_histogram), fib_levels, float(score))
                                        logging.info(f"RSI für {pair}: {rsi_value}")
                                    else:
                                        logging.warning(f"Nicht genügend Daten für {pair}, um den gewichteten Score zu berechnen.")
                                else:
                                    logging.warning(f"Nicht genügend Preisdaten für {pair} vorhanden: {len(prices)}")
                            except Exception as e:
                                logging.error(f"Fehler bei der Datenbankoperation für {pair}: {e}")
                        else:
                            logging.warning(f"Datenbankverbindung nicht verfügbar. Daten für {pair} werden nicht gespeichert.")
                    else:
                        logging.info(f"Keine Rate-Daten für {pair} erhalten.")
                except Exception as e:
                    logging.error(f"Fehler bei der API-Anfrage für {pair}: {e}")
            last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.update_last_update_time(last_update_time)
    
        threading.Thread(target=fetch_and_store, daemon=True).start()

    def update_rsi(self, trading_pair, rsi_value, sma_value, bb_sma, bb_upper, bb_lower, stochastic_value, macd_line, signal_line, macd_histogram, fib_levels, score):
        bb_sma_str = f"{float(bb_sma):.2f}" if bb_sma is not None else "N/A"
        bb_upper_str = f"{float(bb_upper):.2f}" if bb_upper is not None else "N/A"
        bb_lower_str = f"{float(bb_lower):.2f}" if bb_lower is not None else "N/A"
        stochastic_str = f"{float(stochastic_value):.2f}" if stochastic_value is not None else "N/A"
        macd_line_str = f"{float(macd_line):.2f}" if macd_line is not None else "N/A"
        signal_line_str = f"{float(signal_line):.2f}" if signal_line is not None else "N/A"
        macd_histogram_str = f"{float(macd_histogram):.2f}" if macd_histogram is not None else "N/A"
        fib_levels_str = ", ".join([f"{key}: {float(value):.2f}" for key, value in fib_levels.items()]) if fib_levels is not None else "N/A"
    
        # Überprüfen, ob das Trading-Pair bereits in der Treeview vorhanden ist
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == trading_pair:
                self.tree.item(item, values=(trading_pair, rsi_value, sma_value, bb_sma_str, bb_upper_str, bb_lower_str, stochastic_str, macd_line_str, signal_line_str, macd_histogram_str, fib_levels_str, score))
                return
    
        # Wenn das Trading-Pair nicht vorhanden ist, füge es hinzu
        self.tree.insert("", "end", values=(trading_pair, rsi_value, sma_value, bb_sma_str, bb_upper_str, bb_lower_str, stochastic_str, macd_line_str, signal_line_str, macd_histogram_str, fib_levels_str, score))

    def update_last_update_time(self, last_update_time):
        self.last_update_label.config(text=f"Last Update: {last_update_time}")

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.insert(END, msg + '\n')
            self.text_widget.yview(END)
        self.text_widget.after(0, append)

if __name__ == "__main__":
    root = Tk()
    app = CryptoRsiApp()
    gui = CryptoRsiGUI(root, "", app)
    root.mainloop()
