import os
import logging
import json
from pathlib import Path
from cryptography.fernet import Fernet

class CredentialsManager:
    def __init__(self, logger):
        self.logger = logger
        self.config_dir = Path(os.path.dirname(os.path.abspath(__file__)))  # Use the program directory
        #self.config_dir = Path(os.path.expanduser('~/.bitcoin_assistent')) # Use the User's home directory
        self.config_file = self.config_dir / 'config.encrypted'
        self.key_file = self.config_dir / 'key.bin'
        self._ensure_config_dir()
        self._load_or_create_key()
        
    def _ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_or_create_key(self):
        if not self.key_file.exists():
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
        self.key = Fernet(self.key_file.read_bytes())

    def save_credentials(self, api_key: str, api_secret: str, api_basic: str, db_config: dict) -> bool:
        try:
            if self.config_file.exists():
                encrypted_data = self.config_file.read_bytes()
                decrypted_data = self.key.decrypt(encrypted_data)
                config_data = json.loads(decrypted_data.decode())
            else:
                config_data = {}
    
            config_data.update({
                'api_key': api_key,
                'api_secret': api_secret,
                'api_basic': api_basic,
                'db_config': db_config
            })
    
            encrypted_data = self.key.encrypt(json.dumps(config_data).encode())
            self.config_file.write_bytes(encrypted_data)
            self.logger.info("Credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save credentials: {str(e)}")
            return False
            
    def load_credentials(self) -> tuple[str, str, str, dict]:
        try:
            encrypted_data = self.config_file.read_bytes()
            decrypted_data = self.key.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            self.logger.info("Credentials loaded successfully")
            return (
                credentials.get('api_key', ''),
                credentials.get('api_secret', ''),
                credentials.get('api_basic', ''),
                credentials.get('db_config', {})
            )
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {str(e)}")
            return '', '', '', {}

    def save_activation_status(self, status: str) -> bool:
        try:
            if not self.config_file.exists():
                # Erstellen Sie eine leere Konfigurationsdatei, wenn sie nicht existiert
                self.save_credentials('', '', '', {})
            encrypted_data = self.config_file.read_bytes()
            decrypted_data = self.key.decrypt(encrypted_data)
            config_data = json.loads(decrypted_data.decode())
            config_data['activation_status'] = status
            encrypted_data = self.key.encrypt(json.dumps(config_data).encode())
            self.config_file.write_bytes(encrypted_data)
            self.logger.info("Activation status saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save activation status: {str(e)}")
            return False

    def load_activation_status(self) -> str:
        try:
            if not self.config_file.exists():
                self.logger.error("Config file does not exist.")
                return 'not_activated'
            encrypted_data = self.config_file.read_bytes()
            decrypted_data = self.key.decrypt(encrypted_data)
            config_data = json.loads(decrypted_data.decode())
            self.logger.info("Activation status loaded successfully")
            return config_data.get('activation_status', 'not_activated')
        except Exception as e:
            self.logger.error(f"Failed to load activation status: {str(e)}")
            return 'not_activated'