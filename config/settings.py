import os
import logging
from dotenv import load_dotenv
import ssl
import certifi

# configure SSL for macOS before any other imports
if os.name == 'posix' and os.uname().sysname == 'Darwin':
    ssl._create_default_https_context = ssl._create_unverified_context

# load environment variables from .env file
load_dotenv()

# telegram bot configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# database configuration  
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///peptide_bot.db')

# logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__) 