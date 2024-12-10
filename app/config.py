import os
from configparser import ConfigParser
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Set up paths and load environment variables
        self.config_folder = "lite_driver_dot_in"
        self.config_file = "config.ini"
        self.env_file = ".env"

        self.PARSER = ConfigParser()

        self.user_directory = os.path.expanduser("~")
        self.user_data_path = os.path.join(self.user_directory, "data_requirements")
        self.config_path = os.path.join(self.user_data_path, self.config_folder)

        self.create_directory(self.config_path) # Create the directory if it doesn't exist

        # Build full paths for .ini and .env files
        self.ini_path = os.path.join(self.config_path, self.config_file)
        self.env_path = os.path.join(self.config_path, self.env_file)

        # Load environment variables from .env file
        load_dotenv(self.env_path)

        # Ensure config file exists
        if not os.path.exists(self.ini_path):
            print(f"Configuration file not found: {self.ini_path}")

        # Read the .ini file
        self.PARSER.read(self.ini_path)

        # Load values from environment or config file
        self.client_id = os.getenv("client-id") or self.PARSER.get('google', 'client-id', fallback=None)
        self.client_secret = os.getenv("client-secret") or self.PARSER.get('google', 'client-secret', fallback=None)
        self.redirect_url = self.PARSER.get('settings', 'redirect_url', fallback=None)
        self.ip_address = self.PARSER.get('settings', 'ip_address', fallback='0.0.0.0')  # Default to 0.0.0.0 if not set
        self.port = int(self.PARSER.get('settings', 'port', fallback=5000))

        if not self.client_id or not self.client_secret:
                raise ValueError("Client ID or Secret Key not found in environment or config.")

    @staticmethod
    def create_directory(config_path):
        """Ensure that the directory for config files exists."""
        os.makedirs(config_path, exist_ok=True)
