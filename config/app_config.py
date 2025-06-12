# config/app_config.py
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists (for local development)
# In a Docker environment, these are typically passed directly.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # Assuming .env is in project root
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Config:
    # Application settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key-keep-it-safe') # For Flask sessions, etc.
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1' # FLASK_DEBUG=1 for True
    TESTING = os.getenv('TESTING', '0') == '1'

    # Database configuration
    # Prefer DATABASE_URL if available, otherwise construct from components
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
        POSTGRES_USER = os.getenv('POSTGRES_USER', 'n8n_user')
        POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'n8n_password')
        POSTGRES_DB = os.getenv('POSTGRES_DB', 'n8n_db')
        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL # For Flask-SQLAlchemy, if used
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_URL = f"redis://{':' + REDIS_PASSWORD + '@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"


    # Add other application-specific configurations here
    # EXAMPLE_API_KEY = os.getenv('EXAMPLE_API_KEY', 'default_api_key')

# Instantiate the config
# This allows direct import: from config.app_config import settings
settings = Config()

# Example usage (optional, for testing the script directly):
if __name__ == '__main__':
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"Secret Key: {settings.SECRET_KEY}")
