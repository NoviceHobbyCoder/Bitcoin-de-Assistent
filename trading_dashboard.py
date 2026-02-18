import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from loading_screen import LoadingScreen
import logging
from pathlib import Path 
from datetime import datetime
from ui_components import BalancesTab, RatesTab, OrderbookTab, TradingTab, TradeBotTab, LedgerTab, SettingsTab 
from api_client import BitcoinDeApiClient  
from constants import TradingPairs  
from credentials_manager import CredentialsManager 
from database_manager import DatabaseManager  
from sqlite_database_manager import SQLiteDatabaseManager
import os

class TradingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Bind the close event
        self.loading = LoadingScreen()
        self.root.withdraw()  # Hide main window initially
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        self.root.iconbitmap(default=icon_path)  # Setzen des Symbols
        
        try:
            self.initialize_application()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize application: {str(e)}")
            raise
        finally:
            self.root.deiconify()  # Show the main window
            self.loading.finish()

    def on_closing(self):
        """Handle the window close event"""
        # Stop any background processes or threads here
        if hasattr(self, 'orderbook_tab'):
            self.orderbook_tab.stop_auto_updates()
        if hasattr(self, 'rates_tab'):
            self.rates_tab.stop_auto_updates()
        self.root.quit()  # Stop the main loop
        self.root.destroy()  # Destroy the main window

    def initialize_application(self):
        """Initialize all components with loading screen updates"""
        self.loading.update_progress(2, "Erstelle Hauptfenster...")
        self.root.title("Bitcoin de Assistent")
        
        # Dynamisch die Fenstergröße basierend auf der Bildschirmauflösung setzen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)  # 80% der Bildschirmbreite
        window_height = int(screen_height * 0.8)  # 80% der Bildschirmhöhe
        self.root.geometry(f"{window_width}x{window_height}")
        
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        self.root.iconbitmap(default=icon_path)  # Setzen des Symbols

        # Setup logging
        self.loading.update_progress(4, "Setting up logging...")
        self.setup_logging()

        # Initialize credentials manager
        self.loading.update_progress(6, "Initialisiere Zugangsdaten Manager...")
        self.credentials_manager = CredentialsManager(self.logger)
         
        # Load saved credentials
        self.loading.update_progress(10, "Lade gespeicherte Zugangsaten...")
        saved_api_key, saved_api_secret, saved_api_basic, saved_db_config = self.credentials_manager.load_credentials()
        
        # Create StringVar for API credentials
        self.api_key_var = ttk.StringVar(value=saved_api_key)
        self.api_secret_var = ttk.StringVar(value=saved_api_secret)
        self.api_basic_var = ttk.StringVar(value=saved_api_basic)
        
        # Initialize API client
        self.loading.update_progress(20, "Initialisiere API client...")
        self.api_client = BitcoinDeApiClient(
            api_key=self.api_key_var.get(),
            api_secret=self.api_secret_var.get(),
            api_basic=self.api_basic_var.get(),
            logger=self.logger
        )

        # Initialize database manager if config exists
        self.loading.update_progress(30, "Initialisiere Databank...")
        self.db_manager = None
        if saved_db_config:
            try:
                self.db_manager = DatabaseManager(saved_db_config, self.logger)
                self.logger.info("Database manager initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize database manager: {str(e)}")
                self.db_manager = None
                messagebox.showerror("Error", "Failed to initialize database. Check the logs for details.")
        
        

        # Initialize SQLite database manager
        self.sqlite_db_manager = SQLiteDatabaseManager(logger=self.logger)

        # Create main container
        self.loading.update_progress(35, "Erstelle User Interface...")
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(ttk.W, ttk.E, ttk.N, ttk.S))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.grid(row=0, column=0, sticky=(ttk.W, ttk.E, ttk.N, ttk.S))

        # Create frames for tabs
        self.balances_frame = ttk.Frame(self.notebook)
        self.rates_frame = ttk.Frame(self.notebook)
        self.orderbook_frame = ttk.Frame(self.notebook)
        self.trading_frame = ttk.Frame(self.notebook)
        self.trade_bot_frame = ttk.Frame(self.notebook)
        self.ledger_frame = ttk.Frame(self.notebook)  
        self.settings_frame = ttk.Frame(self.notebook)

        # Add frames to notebook
        self.notebook.add(self.balances_frame, text='Kontostände')
        self.notebook.add(self.rates_frame, text='Aktuelle Kurse und Analysen')
        self.notebook.add(self.orderbook_frame, text='Orderbuch')
        self.notebook.add(self.trading_frame, text='Trading')
        self.notebook.add(self.trade_bot_frame, text='Dynamic Trading')
        self.notebook.add(self.ledger_frame, text='Kontoauszüge')  
        self.notebook.add(self.settings_frame, text='Einstellungen')

        # Initialize tab components
        self.loading.update_progress(40, "Initialisierung Interface Komponenten...")
        self.balances_tab = BalancesTab(self.balances_frame, self.logger)
        self.balances_tab.set_update_callback(self.update_balances_only)
        self.rates_tab = RatesTab(self.rates_frame, self.logger, self.db_manager) 
        self.rates_tab.set_update_callback(self.update_rates_only)
        self.orderbook_tab = OrderbookTab(
            parent=self.orderbook_frame,
            logger=self.logger,
            db_manager=self.db_manager,
            api_client=self.api_client    
        )
        # initialize Trading Tab
        self.trading_tab = TradingTab(  
            parent=self.trading_frame,
            logger=self.logger,
            api_client=self.api_client
        )

        self.ledger_tab = LedgerTab(
            self.ledger_frame, 
            self.logger, 
            self.api_client, 
            self.sqlite_db_manager  
        )  

        self.settings_tab = SettingsTab(
            self.settings_frame,
            self.logger,
            self.api_key_var,
            self.api_secret_var,
            self.api_basic_var,
            saved_db_config,
            self.save_credentials
        )

        # TradeBotTab initialisieren
        self.trade_bot_tab = TradeBotTab(
            parent=self.trade_bot_frame,
            logger=self.logger,
            api_client=self.api_client,
            db_manager=self.db_manager
        )

        # Add refresh button (only for non-orderbook data)
        self.refresh_button = ttk.Button(
            self.main_container, 
            text="Kontodaten Aktualisieren",  # Changed text to reflect it only updates account data
            command=self.refresh_account_data
        )        
        self.refresh_button.grid(row=1, column=0, pady=10, sticky='w')

        # Add theme switcher (Toggle Switch)
        self.theme_var = ttk.BooleanVar(value=False)
        self.theme_switcher = ttk.Checkbutton(
            self.main_container,
            text="Dark Mode",
            variable=self.theme_var,
            onvalue=True,
            offvalue=False,
            command=self.toggle_theme,
            bootstyle="switch"
        )
        self.theme_switcher.grid(row=1, column=0, padx=10, pady=10, sticky='e')

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Initial data load if credentials exist
        if saved_api_key and saved_api_secret and saved_api_basic:
            self.loading.update_progress(60, "Lade initial daten...")
            self.refresh_all_data()

        # Finish loading screen after all initializations
        self.loading.finish()
    
    def toggle_theme(self):
        if self.theme_var.get():
            self.root.style.theme_use("darkly")
        else:
            self.root.style.theme_use("cosmo")
    
    def show_info_message(self, title, message):
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        self.root.iconbitmap(default=icon_path)  # Setzen des Symbols
        messagebox.showinfo(title, message, parent=self.root)
    
    def show_error_message(self, title, message):
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        self.root.iconbitmap(default=icon_path)  # Setzen des Symbols
        messagebox.showerror(title, message, parent=self.root)
    
    def show_warning_message(self, title, message):
        icon_path = os.path.join(os.path.dirname(__file__), 'bitcoin.ico')
        self.root.iconbitmap(default=icon_path)  # Setzen des Symbols
        messagebox.showwarning(title, message, parent=self.root)

    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('TradingDashboard')
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        self.logger.setLevel(logging.DEBUG)  
        
        # Create handlers
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)  # Set to DEBUG level
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(stream_handler)
        
        # Prevent propagation to parent loggers (optional, but recommended)
        self.logger.propagate = False
       
    def save_credentials(self, event=None):
        """Save API credentials and database path"""
        api_key = self.api_key_var.get().strip()
        api_secret = self.api_secret_var.get().strip()
        api_basic = self.api_basic_var.get().strip()
        db_config = {
            'host': self.settings_tab.host_var.get().strip(),
            'user': self.settings_tab.user_var.get().strip(),
            'password': self.settings_tab.password_var.get().strip(),
            'database': self.settings_tab.database_var.get().strip(),
            'port': self.settings_tab.port_var.get()
        }
        
        # Validate API credentials
        if not api_key or not api_secret:
            self.logger.warning("Full API key and secret cannot be empty")
            messagebox.showwarning("Warning", "Full API key and secret cannot be empty")
            return
            
        if not api_basic:
            self.logger.warning("Basic API key cannot be empty")
            messagebox.showwarning("Warning", "Basic API key cannot be empty")
            return
        
        # Validate database config
        if not db_config['host'] or not db_config['user'] or not db_config['password'] or not db_config['database']:
            self.logger.warning("Database configuration fields cannot be empty")
            messagebox.showwarning("Warning", "Database configuration fields cannot be empty")
            return
        
        # Save credentials including database config
        if self.credentials_manager.save_credentials(api_key, api_secret, api_basic, db_config):
            self.logger.info("Credentials and database configuration saved successfully")
            
            # Update API client with new credentials
            self.api_client = BitcoinDeApiClient(
                api_key=api_key,
                api_secret=api_secret,
                api_basic=api_basic,
                logger=self.logger
            )
            
            # Update or initialize database manager
            try:
                self.db_manager = DatabaseManager(db_config, self.logger)
                # Update orderbook tab with new database manager
                self.orderbook_tab.set_db_manager(self.db_manager)
                self.logger.info("Database manager updated successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize database manager: {str(e)}")
                messagebox.showerror("Error", "Failed to connect to database")
                return
            
            messagebox.showinfo("Success", "API credentials and database settings saved successfully!")
            
            # Refresh account data with new credentials
            # Note: Orderbook will update automatically through its own mechanism
            self.refresh_account_data()
        else:
            self.logger.error("Failed to save credentials")
            messagebox.showerror("Error", "Failed to save credentials")

    def refresh_account_data(self):
        """Refresh account-related data (balances and rates)"""
        try:
            self.refresh_button.configure(state='disabled')  # Disable button during refresh
            self.logger.info("Starting account data refresh")
            
            # First collect all rates
            if self.api_basic_var.get():
                rates_data = {}
                for pair in TradingPairs.get_all_pairs():
                    try:
                        response = self.api_client.get_basic_rates(pair)
                        if response and 'rate' in response:
                            rates_data[pair] = response
                    except Exception as e:
                        self.logger.error(f"Failed to fetch rates for {pair}: {str(e)}")
                
                # Update rates in balances tab first
                self.loading.update_progress(75, "verarbeite Account information...")
                self.balances_tab.update_rates(rates_data)
            
            # Then update balances
            account_data = self.api_client.get_account_info()
            self.loading.update_progress(95, "Lade Kontostände...")
            self.balances_tab.update_balances(account_data)
            
            # Update rates display
            self.update_rates_only()
            
            self.logger.info("Account data refresh completed")
            
            # Update window title with last refresh time
            self.root.title(
                f"Bitcoin de Assistent - Letztes Update: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            self.logger.error(f"Error refreshing account data: {str(e)}")
            messagebox.showerror("Error", "Failed to refresh account data. Check logs for details.")
        finally:
            self.refresh_button.configure(state='normal')  # Re-enable button
    
    def refresh_all_data(self):
        """Legacy method - now just calls refresh_account_data"""
        self.refresh_account_data()

    def update_balances_only(self):
        """Update only the balances tab data"""
        try:
            account_data = self.api_client.get_account_info()
            self.balances_tab.update_balances(account_data)
            self.root.title(
                f"Bitcoin de Assistent - Balances Updated: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            self.logger.error(f"Error updating balances: {str(e)}")
            messagebox.showerror("Error", "Failed to update balances. Check logs for details.")

    def update_rates_only(self):
        """Update only the rates tab data"""
        try:
            # Refresh rates
            self.logger.debug("Fetching rates...")
            self.rates_tab.clear_rates()
            for pair in TradingPairs.get_all_pairs():
                try:
                    response = self.api_client.get_basic_rates(pair)
                    if response and 'rate' in response:
                        response['trading_pair'] = pair
                        self.rates_tab.update_rates(response)
                except Exception as e:
                    self.logger.error(f"Failed to fetch rates for {pair}: {str(e)}")
            self.logger.info("Rates updated successfully")
            
            # Update window title with last refresh time
            self.root.title(
                f"Bitcoin de Assistent - Rates Updated: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            self.logger.error(f"Error updating rates: {str(e)}")
            messagebox.showerror("Error", "Failed to update rates. Check logs for details.")

if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = TradingDashboard(root)
    root.mainloop()