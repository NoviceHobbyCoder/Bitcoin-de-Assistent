import json
import logging
import threading
import time
import os
import sys
import ctypes
import psutil
import tkinter as tk
from datetime import datetime
from tkinter import Tk
import hashlib
import requests
import mysql.connector
from tkinter import messagebox, ttk
from logging.handlers import RotatingFileHandler
from cryptography.fernet import Fernet
from api_client import ApiClient
from database import Database
from rsi_calculator import RsiCalculator
from sma_calculator import SmaCalculator
from bollinger_bands_calculator import BollingerBandsCalculator
from stochastic_oscillator_calculator import StochasticOscillatorCalculator
from macd_calculator import MacdCalculator
from fibonacci_calculator import FibonacciCalculator
from gui import CryptoRsiGUI

# Sicherheitsmethoden
if not (hasattr(sys, "frozen") or __name__ == "__main__"):
    print("Zugriff verweigert!")
    sys.exit()

def check_debugger():
    """Erkennt, ob ein Debugger aktiv ist und beendet das Programm."""
    if sys.platform == "win32":
        is_debugged = ctypes.windll.kernel32.IsDebuggerPresent()
        if is_debugged:
            print("Debugger erkannt! Beende Programm...")
            sys.exit()

def check_debugger_process():
    """Überprüft, ob Debugging-Tools wie x64dbg, IDA oder Ghidra laufen."""
    suspicious_processes = ["x32dbg.exe", "x64dbg.exe", "ollydbg.exe", "ida64.exe", "ghidra.exe"]
    for process in psutil.process_iter(["name"]):
        if process.info["name"] in suspicious_processes:
            print(f"Verdächtiger Prozess entdeckt: {process.info['name']}! Beende Programm...")
            sys.exit()

check_debugger()
check_debugger_process()

#LICENSE_SERVER_URL = "https://registrierung.btc-de-client.de/register_license"

class CustomLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        log_entry = self.format(record)
        if "Datenbankkonfiguration wurde geändert" in log_entry:
            self.text_widget.insert(tk.END, log_entry + "\n")
            self.text_widget.see(tk.END)

# Konfigurieren des StreamHandlers
log_formatter = logging.Formatter('%(levelname)s - %(message)s')
log_handler = logging.StreamHandler()  # Ausgabe auf die Konsole
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

# Konfigurieren des Root-Loggers
logging.basicConfig(level=logging.INFO, handlers=[log_handler])

class CryptoRsiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyse Server")
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        self.root.iconbitmap(icon_path) 
        self.config_dir = os.path.join(os.path.expanduser("~"), ".Analyse Server")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.activation_file = os.path.join(self.config_dir, "db.config")
        self.key_file = os.path.join(self.config_dir, "key.key")
        self.load_settings()
        self.api_client = ApiClient(self.api_key)
        self.cipher = Fernet(self.load_key())
        
        # Überprüfen, ob alle erforderlichen Datenbankverbindungsdaten vorhanden sind
        if all([self.db_name, self.db_user, self.db_password, self.db_host, self.db_port]):
            try:
                self.database = Database(
                    db_name=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    host=self.db_host,
                    port=self.db_port
                )
                logging.info("Erfolgreich mit der Datenbank verbunden.")
            except mysql.connector.Error as err:
                logging.error(f"Fehler bei der Initialisierung der Datenbank: {err}")
                self.database = None
            except Exception as e:
                logging.error(f"Allgemeiner Fehler bei der Initialisierung der Datenbank: {e}")
                self.database = None
        else:
            logging.warning("Unvollständige Datenbankverbindungsdaten. Datenbank wird nicht initialisiert.")
            self.database = None

        self.rsi_calculator = RsiCalculator()
        self.sma_calculator = SmaCalculator()
        self.bollinger_bands_calculator = BollingerBandsCalculator()
        self.stochastic_oscillator_calculator = StochasticOscillatorCalculator()
        self.macd_calculator = MacdCalculator()
        self.fibonacci_calculator = FibonacciCalculator()
        self.trading_pairs = ["btceur", "bcheur", "etheur", "soleur", "xrpeur", "ltceur", "dogeeur", "btgeur", "trxeur", "usdceur"]

        # Lizenzabfrage
        """
        activation_status = self.load_activation_status()
        if activation_status != '127.0.0.1':
            self.ask_license_key()
        else:
            """
        self.root.deiconify()  # Zeige das Hauptfenster, wenn die Lizenz bereits aktiviert ist
    """
    def load_activation_status(self):
        ###Load activation status from a separate file###
        try:
            with open(self.activation_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                config = json.loads(decrypted_data)
                return config.get('activation_status', '192.168.0.1')
        except (FileNotFoundError, json.JSONDecodeError):
            return '192.168.0.1'

    def save_activation_status(self, status):
        ###Save activation status to a separate file###
        config = {'activation_status': status}
        with open(self.activation_file, 'wb') as f:
            data = json.dumps(config).encode()
            encrypted_data = self.cipher.encrypt(data)
            f.write(encrypted_data)

    def activate_program(self, license_key):
        if self.register_license_key(license_key):
            self.save_activation_status('127.0.0.1')
            return True
        else:
            return False

    def ask_license_key(self):
        ###Ask the user for the license key in a custom dialog with one input field.###
        def on_submit():
            license_key = entry.get()
            if self.activate_program(license_key):
                messagebox.showinfo("Registrierung erfolgreich", "Programm erfolgreich aktiviert - Vielen Dank.")
                dialog.destroy()
                self.root.deiconify()  # Zeige das Hauptfenster nach erfolgreicher Aktivierung
            else:
                messagebox.showerror("Fehler", "Ungültiger Schlüssel oder Registrierung fehlgeschlagen. Kontaktieren sie den Support! Programm wird beendet.")
                dialog.destroy()
                self.root.destroy()
    
        dialog = tk.Toplevel(self.root)
        dialog.title("Analyse-Server Lizenzschlüssel eingeben")
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        dialog.iconbitmap(icon_path)  # Setzen des Symbols
    
        ttk.Label(dialog, text="Bitte geben Sie Ihren Analyse-Server Lizenzschlüssel ein:").pack(pady=10)
    
        entry = ttk.Entry(dialog, width=40, font=('Arial', 14))
        entry.pack(pady=10)
    
        submit_button = ttk.Button(dialog, text="Einreichen", command=on_submit)
        submit_button.pack(pady=10)
    
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_set()
        
        # Schließe die Anwendung, wenn das Lizenzabfragefenster geschlossen wird
        dialog.protocol("WM_DELETE_WINDOW", self.root.destroy)
        
        dialog.wait_window(dialog)

        # Verstecke das Hauptfenster, nachdem das Lizenzabfragefenster angezeigt wurde
        self.root.withdraw()

    def register_license_key(self, license_key):
        device_id = self.get_device_id()
        try:
            response = requests.post(LICENSE_SERVER_URL, json={
                "license_key": license_key,
                "device_id": device_id
            })  # Entfernen von verify=False, um die Zertifikatsüberprüfung zu aktivieren
            result = response.json()
            if response.status_code == 200 and result.get("status") == "success":
                return True
            else:
                return False
        except requests.RequestException as e:
            logging.error(f"Failed to register license key: {str(e)}")
            return False

    def get_device_id(self):
        ###Generiert eine eindeutige Geräte-ID (basiert auf MAC-Adresse)###
        return hashlib.sha256("example_device_id".encode()).hexdigest()
    """
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

    def load_settings(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if not os.path.exists(self.key_file):
            self.generate_key()
        try:
            with open(self.config_file, 'rb') as config_file:
                encrypted_data = config_file.read()
                decrypted_data = self.decrypt_data(encrypted_data)
                settings = json.loads(decrypted_data)
                self.api_key = settings.get('api_key', '')
                self.db_name = settings.get('db_name', 'crypto_data')
                self.db_user = settings.get('db_user', '')
                self.db_password = settings.get('db_password', '')
                self.db_host = settings.get('db_host', 'localhost')
                self.db_port = int(settings.get('db_port', 3306))
        except FileNotFoundError:
            logging.warning("No settings file found.")
            self.api_key = ''
            self.db_name = 'crypto_data'
            self.db_user = ''
            self.db_password = ''
            self.db_host = 'localhost'
            self.db_port = 3306
        except Exception as e:
            logging.error(f"Fehler beim Laden der Einstellungen: {e}")
            self.api_key = ''
            self.db_name = 'crypto_data'
            self.db_user = ''
            self.db_password = ''
            self.db_host = 'localhost'
            self.db_port = 3306

    def save_settings(self, settings):
        try:
            data = json.dumps(settings)
            encrypted_data = self.encrypt_data(data)
            with open(self.config_file, 'wb') as config_file:
                config_file.write(encrypted_data)
            logging.info("Settings saved.")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Einstellungen: {e}")

    def fetch_and_store_data(self, interval):
        for pair in self.trading_pairs:
            try:
                rates = self.api_client.get_basic_rates(pair)
                if rates and 'rate' in rates:
                    rate_weighted = float(rates['rate']['rate_weighted'])
                    if self.database:
                        try:
                            self.database.insert_price(pair, rate_weighted, interval)
                            prices = self.database.fetch_prices(pair, interval)
                            if len(prices) > 160:  # Limitiere die Anzahl der gespeicherten Preise auf 160
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
                                    score = self.calculate_weighted_score(current_price, rsi_value, macd_line, signal_line, bb_sma, bb_upper, bb_lower, stochastic_value, fib_levels)
                                    self.database.update_weighted_score(pair, float(score), interval)
                                    self.update_gui(pair, float(rsi_value), float(sma_value), float(bb_sma), float(bb_upper), float(bb_lower), float(stochastic_value), float(macd_line), float(signal_line), float(macd_histogram), fib_levels, float(score))
                                    logging.info(f"RSI für {pair} mit Intervall {interval}: {rsi_value}")
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
        self.update_last_update_time()
    
    def start_data_fetching(self):
        threading.Thread(target=self.fetch_data_interval, args=(1800, '30m'), daemon=True).start()  # 30 Minuten (halber Tag = 13 Stunden)
        threading.Thread(target=self.fetch_data_interval, args=(3600, '1h'), daemon=True).start()  # 1 Stunde (ein Tag = 26 Stunden)
        threading.Thread(target=self.fetch_data_interval, args=(28800, '8h'), daemon=True).start()  # 8 Stunden (8Tage 16 Stunden)
        threading.Thread(target=self.fetch_data_interval, args=(86400, '24h'), daemon=True).start()  # 24 Stunden (26 Tage)
    
    def fetch_data_interval(self, interval, interval_label):
        while True:
            self.fetch_and_store_data(interval_label)
            time.sleep(interval)

    def calculate_rsi_score(self, rsi, trend):
        if trend == "bullish":
            return 1 if rsi < 40 else (-1 if rsi > 80 else 0)
        elif trend == "bearish":
            return 1 if rsi < 20 else (-1 if rsi > 60 else 0)
        else:  # Seitwärtsmarkt
            return 1 if rsi < 30 else (-1 if rsi > 70 else 0)

    def calculate_weighted_score(self, current_price, rsi_value, macd_line, signal_line, bb_sma, bb_upper, bb_lower, stochastic_value, fib_levels):
        score = 0

        # Bestimme den Trend basierend auf dem MACD
        if macd_line is not None and signal_line is not None:
            if macd_line > 0:
                trend = "bullish"
            elif macd_line < 0:
                trend = "bearish"
            else:
                trend = "sideways"
        else:
            trend = "sideways"

        # RSI Score
        score += self.calculate_rsi_score(rsi_value, trend)

        # MACD Score
        if macd_line is not None and signal_line is not None:
            if macd_line > signal_line:
                score += 1
            elif macd_line < signal_line:
                score -= 1

        # Bollinger Bands Score
        if bb_sma is not None and bb_upper is not None and bb_lower is not None:
            if bb_sma < bb_lower:
                score += 1
            elif bb_sma > bb_upper:
                score -= 1

        # Stochastic Oscillator Score
        if stochastic_value is not None:
            if stochastic_value < 20:
                score += 1
            elif stochastic_value > 80:
                score -= 1

        # Fibonacci Score
        if fib_levels is not None:
            if current_price < fib_levels["23.6%"]:
                score += 1
            elif current_price > fib_levels["78.6%"]:
                score -= 1

        # Begrenze den Score auf den Bereich -3 bis +3
        score = max(-3, min(3, score))

        return score

    def update_gui(self, trading_pair, rsi_value, sma_value, bb_sma, bb_upper, bb_lower, stochastic_value, macd_line, signal_line, macd_histogram, fib_levels, score):
        self.gui.update_rsi(trading_pair, rsi_value, sma_value, bb_sma, bb_upper, bb_lower, stochastic_value, macd_line, signal_line, macd_histogram, fib_levels, score)

    def update_last_update_time(self):
        last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"Last Update: {last_update_time}")
        if self.gui:
            self.gui.update_last_update_time(last_update_time)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = Tk()
    root.geometry("900x400")  # Setzen Sie die gewünschte Größe des Hauptfensters
    app = CryptoRsiApp(root)
    gui = CryptoRsiGUI(root, app.api_key, app)
    app.gui = gui  # Referenz zur GUI in der App speichern
    threading.Thread(target=app.start_data_fetching, daemon=True).start()
    root.mainloop()