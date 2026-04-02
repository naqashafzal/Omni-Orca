import json
import os
from cryptography.fernet import Fernet

CONFIG_FILE = "config.json"
KEY_FILE = ".secret.key"

class ConfigManager:
    def __init__(self):
        self.config = {
            "api_key": "",
            "theme": "Dark",
            "model_name": "gemini-2.5-flash",
            "accounts": {} # Encrypted credentials storage
        }
        self._load_key()
        self.load_config()

    def _load_key(self):
        """Load or generate encryption key."""
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as key_file:
                self.key = key_file.read()
        else:
            self.key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as key_file:
                key_file.write(self.key)
        self.cipher = Fernet(self.key)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key):
        return self.config.get(key)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def encrypt(self, text):
        if not text: return ""
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, token):
        if not token: return ""
        try:
            return self.cipher.decrypt(token.encode()).decode()
        except:
            return ""

    def save_account(self, platform, username, password):
        """Save encrypted account credentials."""
        if "accounts" not in self.config:
            self.config["accounts"] = {}
        
        self.config["accounts"][platform] = {
            "username": username,
            "password": self.encrypt(password)
        }
        self.save_config()

    def get_account(self, platform):
        """Get decrypted account credentials."""
        if "accounts" not in self.config or platform not in self.config["accounts"]:
            return None
        
        data = self.config["accounts"][platform]
        return {
            "username": data["username"],
            "password": self.decrypt(data["password"])
        }
    
    def get_all_accounts(self):
        """Return list of platforms."""
        return list(self.config.get("accounts", {}).keys())
