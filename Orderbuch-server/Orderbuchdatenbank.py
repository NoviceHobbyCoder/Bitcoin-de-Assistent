# Mysql Orderbuchdatenbank.py
import os
import sys
import ctypes
import psutil
import hashlib
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from websocket_client import WebSocketClient
from database_handler import DatabaseHandler
from cryptography.fernet import Fernet
import threading
import queue
import time
import json

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

class OrderbuchDatenbank:
    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        self.root.title("Orderbuch Datenbank Live")
        self.root.geometry("1200x800")  # Increased window size

        # Set custom window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        self.root.iconbitmap(icon_path)

        # Setup logging (without file handler)
        self.setup_logging()
        
        # Generate or load encryption key
        self.key = self.load_key()
        self.cipher = Fernet(self.key)

        # Load MySQL configuration from file
        self.db_config = self.load_db_config()

        self.logger = logging.getLogger('OrderbuchDatenbank')

        # Check activation status
        """
        if not self.is_activated():
            self.ask_license_key()
        """
        # Initialize DatabaseHandler
        try:
            self.db_handler = DatabaseHandler(self.logger, self.db_config)  # Use db_config here
            self.logger.debug(f"DatabaseHandler initialized: {self.db_handler is not None}")
        except Exception as e:
            self.logger.error(f"Failed to initialize DatabaseHandler: {str(e)}")
            self.db_handler = None

        # Initialize components without database connection
        self.ws_client = WebSocketClient(
            callback=self.handle_ws_message,
            logger=self.logger,
            db_handler=self.db_handler  # Pass the db_handler here
        )
        self.logger.debug(f"WebSocketClient initialized with db_handler: {self.ws_client.db_handler is not None}")

        # Message queue for thread-safe GUI updates
        self.msg_queue = queue.Queue()
        self.max_log_lines = 1000  # Limit log lines
        
        self.setup_ui()
        self.start_queue_processing()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_key(self):
        """Load or generate encryption key"""
        user_dir = os.path.expanduser("~")
        config_dir = os.path.join(user_dir, '.Orderbuch-Server')
        os.makedirs(config_dir, exist_ok=True)
        key_file = os.path.join(config_dir, 'secret.key')
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    """
    def load_activation_status(self):
        ###Load activation status from file###
        user_dir = os.path.expanduser("~")
        config_dir = os.path.join(user_dir, '.Orderbuch-Server')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'config.json')
        try:
            with open(config_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                config = json.loads(decrypted_data)
                return config.get('activation_status', '192.168.0.1')
        except (FileNotFoundError, json.JSONDecodeError):
            return '192.168.0.1'
    
    def save_activation_status(self, status):
        ###Save activation status to file###
        user_dir = os.path.expanduser("~")
        config_dir = os.path.join(user_dir, '.Orderbuch-Server')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'config.json')
        config = {'activation_status': status}
        with open(config_file, 'wb') as f:
            data = json.dumps(config).encode()
            encrypted_data = self.cipher.encrypt(data)
            f.write(encrypted_data)
    """
    def load_db_config(self):
        """Load database configuration from file"""
        user_dir = os.path.expanduser("~")
        config_dir = os.path.join(user_dir, '.Orderbuch-Server')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'db_config.json')
        try:
            with open(config_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                config = json.loads(decrypted_data)
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'host': '',
                'user': '',
                'password': '',
                'database': ''
            }
    
    def save_db_config(self, config):
        """Save database configuration to file"""
        user_dir = os.path.expanduser("~")
        config_dir = os.path.join(user_dir, '.Orderbuch-Server')
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, 'db_config.json')
        with open(config_file, 'wb') as f:
            data = json.dumps(config).encode()
            encrypted_data = self.cipher.encrypt(data)
            f.write(encrypted_data)
    """
    def is_activated(self):
        return self.load_activation_status() == '127.0.0.1'
    
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
                root.destroy()
            else:
                messagebox.showerror("Fehler", "Ungültiger Schlüssel oder Registrierung fehlgeschlagen. Kontaktieren sie den Support! Programm wird beendet.")
                root.destroy()
                self.root.destroy()
    
        def on_close():
            ###Handle the closing of the license key window.###
            self.root.destroy()
    
        root = tk.Toplevel(self.root)
        root.title("Orderbuch-Server Lizenzschlüssel eingeben")
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        root.iconbitmap(icon_path)  # Setzen des Symbols
    
        ttk.Label(root, text="Bitte geben Sie Ihren Ordrbuch-Server Lizenzschlüssel ein:").pack(pady=10)
    
        entry = ttk.Entry(root, width=40, font=('Arial', 14))
        entry.pack(pady=10)
    
        submit_button = ttk.Button(root, text="Einreichen", command=on_submit)
        submit_button.pack(pady=10)
    
        root.protocol("WM_DELETE_WINDOW", on_close)  # Handle window close event
    
        root.transient(self.root)
        root.grab_set()
        root.mainloop()
    
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
            self.logger.error(f"Failed to register license key: {str(e)}")
            return False
    
    def get_device_id(self):
        ###Generiert eine eindeutige Geräte-ID (basiert auf MAC-Adresse)###
        return hashlib.sha256("example_device_id".encode()).hexdigest()
    """
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Einstellungen")
        settings_window.geometry("400x250")
        settings_window.transient(self.root)
        settings_window.grab_set()
    
        # Set custom window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        settings_window.iconbitmap(icon_path)
    
        # Create and pack widgets
        frame = ttk.Frame(settings_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
        # MySQL settings
        ttk.Label(frame, text="MySQL Host:").grid(row=0, column=0, sticky=tk.W)
        host_var = tk.StringVar(value=self.db_config['host'])
        host_entry = ttk.Entry(frame, textvariable=host_var, width=40)
        host_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
    
        ttk.Label(frame, text="MySQL Benutzer:").grid(row=1, column=0, sticky=tk.W)
        user_var = tk.StringVar(value=self.db_config['user'])
        user_entry = ttk.Entry(frame, textvariable=user_var, width=40)
        user_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
    
        ttk.Label(frame, text="MySQL Passwort:").grid(row=2, column=0, sticky=tk.W)
        password_var = tk.StringVar(value=self.db_config['password'])
        password_entry = ttk.Entry(frame, textvariable=password_var, width=40, show="*")
        password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))
    
        ttk.Label(frame, text="MySQL Datenbank:").grid(row=3, column=0, sticky=tk.W)
        database_var = tk.StringVar(value=self.db_config['database'])
        database_entry = ttk.Entry(frame, textvariable=database_var, width=40)
        database_entry.grid(row=3, column=1, sticky=(tk.W, tk.E))
    
        def save_settings():
            try:
                new_config = {
                    'host': host_var.get(),
                    'user': user_var.get(),
                    'password': password_var.get(),
                    'database': database_var.get()
                }
                self.save_db_config(new_config)
    
                # Close current database connection if exists
                if hasattr(self, 'db_handler') and self.db_handler:
                    self.db_handler.close()
    
                # Create new database handler with new config
                self.db_handler = DatabaseHandler(self.logger, new_config)
                self.ws_client.db_handler = self.db_handler
    
                self.msg_queue.put("Datenbankkonfiguration geändert")
    
                # Update UI with new database status
                self.update_statistics()
    
                settings_window.destroy()  # Fenster automatisch schließen
    
            except Exception as e:
                self.msg_queue.put(f"Error changing database configuration: {str(e)}")
            finally:
                self.logger.info("Datenbankkonfiguration wurde geändert")
    
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
    
        save_button = ttk.Button(
            button_frame,
            text="Speichern",
            command=save_settings
        )
        save_button.pack(side=tk.LEFT, padx=5)
    
        cancel_button = ttk.Button(
            button_frame,
            text="Schließen",
            command=settings_window.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
        # Configure grid weights
        settings_window.columnconfigure(0, weight=1)
        settings_window.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('OrderbuchDatenbank')
        self.logger.setLevel(logging.INFO)
    
        # Only console handler, no file handler
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # Korrigiert: levelname statt levellevel
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def setup_ui(self):
        """Setup the GUI components"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="WebSocket Status", padding="5")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Status: Nicht verbunden")
        self.status_label.grid(row=0, column=0, padx=5)
        
        # Custom styled button for connection status
        self.connect_button = tk.Button(
            status_frame,
            text="Verbinden",
            command=self.toggle_connection,
            bg='#ff6b6b',  # Red background
            fg='white',    # White text
            relief=tk.RAISED,
            width=10,
            height=1
        )
        self.connect_button.grid(row=0, column=1, padx=5)

        self.settings_button = ttk.Button(
            status_frame,
            text="Einstellungen",
            command=self.show_settings
        )
        self.settings_button.grid(row=0, column=2, padx=5)
        
        # Database section
        db_frame = ttk.LabelFrame(main_frame, text="Datenbank Status", padding="5")
        db_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.orders_count_label = ttk.Label(db_frame, text="Orders in DB: 0")
        self.orders_count_label.grid(row=0, column=0, padx=5)
        
        # Trading pairs in a scrollable frame
        pairs_frame = ttk.LabelFrame(main_frame, text="Handelspaare", padding="5")
        pairs_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create canvas and scrollbar for trading pairs
        canvas = tk.Canvas(pairs_frame, height=100)
        scrollbar = ttk.Scrollbar(pairs_frame, orient="horizontal", command=canvas.xview)
        self.pairs_container = ttk.Frame(canvas)
        
        canvas.configure(xscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Create window in canvas for pairs
        canvas_frame = canvas.create_window((0, 0), window=self.pairs_container, anchor="nw")
        
        # Trading pairs
        self.pair_labels = {}
        trading_pairs = [
            'btceur', 'etheur', 'ltceur', 'bcheur', 'xrpeur', 
            'dogeeur', 'soleur', 'btgeur', 'trxeur','usdceur'
        ]
        
        for i, pair in enumerate(trading_pairs):
            frame = ttk.Frame(self.pairs_container)
            frame.grid(row=0, column=i, padx=5)
            
            label = ttk.Label(frame, text=f"{pair.upper()}\n0 Orders")
            label.pack()
            self.pair_labels[pair] = label
        
        # Update canvas scroll region when pairs container changes
        self.pairs_container.bind('<Configure>', 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Log section with limited lines
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_frame, height=20, width=100)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        pairs_frame.columnconfigure(0, weight=1)

    def start_queue_processing(self):
        """Start processing the message queue"""
        self.process_queue()
        self.update_statistics()

    def process_queue(self):
        """Process messages from the queue"""
        try:
            while True:
                message = self.msg_queue.get_nowait()
                
                # Limit log lines
                lines = self.log_text.get('1.0', tk.END).splitlines()
                if len(lines) > self.max_log_lines:
                    self.log_text.delete('1.0', f"{len(lines) - self.max_log_lines}.0")
                
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def update_statistics(self):
        """Update statistics display"""
        try:
            if self.db_handler:
                # Update total orders count
                total_count = self.db_handler.get_orders_count()
                self.orders_count_label.config(text=f"Orders in DB: {total_count}")

                # Update trading pair statistics
                for pair in self.pair_labels:
                    count = self.db_handler.get_orders_count_by_pair(pair)
                    self.pair_labels[pair].config(text=f"{pair.upper()}\n{count} Orders")
            else:
                self.orders_count_label.config(text="Orders in DB: N/A")
                for pair in self.pair_labels:
                    self.pair_labels[pair].config(text=f"{pair.upper()}\nN/A")
        except Exception as e:
            self.msg_queue.put(f"Error updating statistics: {str(e)}")
        finally:
            self.root.after(1000, self.update_statistics)

    def update_connection_status(self, connected):
        """Update connection status display"""
        self.ws_connected = connected
        self.status_label.config(
            text=f"Status: {'Verbunden' if connected else 'Nicht verbunden'}"
        )
        
        # Update button text and color
        if connected:
            self.connect_button.config(
                text="Trennen",
                bg='#51cf66',  # Green
                state='normal'
            )
        else:
            self.connect_button.config(
                text="Verbinden",
                bg='#ff6b6b',  # Red
                state='normal'
            )

    def toggle_connection(self):
        """Toggle WebSocket connection"""
        if not hasattr(self, 'ws_connected') or not self.ws_connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        """Connect to WebSocket"""
        def connect_thread():
            try:
                self.ws_client.connect()
                self.msg_queue.put("WebSocket verbunden")
                self.root.after(0, self.update_connection_status, True)
            except Exception as e:
                self.msg_queue.put(f"Verbindung fehlgeschlagen: {str(e)}")
                self.root.after(0, self.update_connection_status, False)

        self.connect_button.config(state='disabled')
        threading.Thread(target=connect_thread, daemon=True).start()

    def disconnect(self):
        """Disconnect from WebSocket"""
        try:
            self.ws_client.disconnect()
            self.msg_queue.put("WebSocket getrennt")
            self.update_connection_status(False)
        except Exception as e:
            self.msg_queue.put(f"Fehler beim Trennen: {str(e)}")

    def handle_ws_message(self, data):
        """Handle incoming WebSocket messages"""
        try:
            if data:
                action = data.get('action')
                order = data.get('order')
            
                if action == 'add':
                    self.msg_queue.put(f"Neues Order erhalten: {order.get('order_id')} ({order.get('trading_pair', 'unknown')})")
                elif action == 'remove':
                    self.msg_queue.put(f"Order entfernt: {order.get('order_id')} ({order.get('trading_pair', 'unknown')})")
   
        except Exception as e:
            self.msg_queue.put(f"Error processing message: {str(e)}")
            self.log_text.tag_configure("error", foreground="red")
            self.log_text.insert(tk.END, f"Error processing message: {str(e)}\n", "error")

    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Beenden", "Möchten Sie die Anwendung wirklich beenden?"):
            self.cleanup()
            self.root.destroy()

    def run(self):
        """Start the application"""
        try:
            self.logger.info("Starte Orderbuch Datenbank...")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Anwendungsfehler: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'ws_client'):
                self.ws_client.disconnect()
            if hasattr(self, 'db_handler'):
                self.db_handler.close()
            self.logger.info("Anwendung beendet")
        except Exception as e:
            self.logger.error(f"Fehler beim Beenden: {str(e)}")

if __name__ == "__main__":
    app = OrderbuchDatenbank()
    app.run()
