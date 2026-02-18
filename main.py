import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import simpledialog, messagebox
from trading_dashboard import TradingDashboard
import logging
import requests
from credentials_manager import CredentialsManager
import sys
import ctypes  
import psutil  
import hashlib

# Configure the global logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])

# Example usage
logger = logging.getLogger(__name__)
logger.debug("This is a debug message")

# Blockiere direkten Import nur, wenn es in einer kompilierten Umgebung läuft
if not (hasattr(sys, "frozen") or __name__ == "__main__"):
    print("Zugriff verweigert!")
    sys.exit()

# Debugger-Erkennung
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

# Debugging-Prüfung direkt beim Start durchführen
check_debugger()
check_debugger_process()

# Initialisieren des Loggers
logger = logging.getLogger(__name__)

# Initialisieren des Credentials Managers
credentials_manager = CredentialsManager(logger)

# Klartext-URL des Lizenzservers
#LICENSE_SERVER_URL = "https://registrierung.btc-de-client.de/register_license"

def setup_logging():
    """Setup basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )

"""
def register_license_key(license_key):
    device_id = get_device_id()
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

def get_device_id():
    ###Generiert eine eindeutige Geräte-ID (basiert auf MAC-Adresse)###
    return hashlib.sha256("example_device_id".encode()).hexdigest()

def is_activated():
    return credentials_manager.load_activation_status() == "activated"

def activate_program(license_key):
    if register_license_key(license_key):
        credentials_manager.save_activation_status("activated")
        return True
    else:
        return False

def ask_license_key():
    ###Ask the user for the license key in a custom dialog with one input field.###
    def on_submit():
        license_key = entry.get()
        if activate_program(license_key):
            messagebox.showinfo("Registrierung erfolgreich", "Programm erfolgreich aktiviert - Vielen Dank.")
            root.destroy()
        else:
            messagebox.showerror("Fehler", "Ungültiger Schlüssel oder Registrierung fehlgeschlagen. Kontaktieren sie den Support! Programm wird beendet.")
            root.destroy()

    root = ttk.Window(themename="cosmo")
    root.title("Lizenzschlüssel eingeben")
    icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
    root.iconbitmap(default=icon_path)  # Setzen des Symbols

    ttk.Label(root, text="Bitte geben Sie Ihren Lizenzschlüssel ein:").pack(pady=10)

    entry = ttk.Entry(root, width=30, font=('Arial', 14))
    entry.pack(pady=10)

    submit_button = ttk.Button(root, text="Einreichen", command=on_submit)
    submit_button.pack(pady=10)

    root.mainloop()
"""
def main():
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        """
        if is_activated():
            print("Programm ist bereits aktiviert.")
        else:
            ask_license_key()
            return
        """
        # Erneute Debugging-Prüfung beim Start
        check_debugger()
        check_debugger_process()

        # Create main window
        root = ttk.Window(themename="cosmo")
        root.title("Bitcoin de Assistent")
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        root.iconbitmap(default=icon_path)  # Setzen des Symbols

        # Create dashboard
        app = TradingDashboard(root)

        # Start the application
        logger.info("Starting application...")
        root.mainloop()

    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        raise

if __name__ == "__main__":
    main()