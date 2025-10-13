import os

# Bitkub API
BITKUB_API_KEY = os.getenv('BITKUB_API_KEY', 'your_api_key')
BITKUB_API_SECRET = os.getenv('BITKUB_API_SECRET', 'your_secret')
BITKUB_API_URL = 'https://api.bitkub.com'

# MySQL Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'bot_trade')

# Trading Settings
SYMBOLS = ['THB_BTC', 'THB_ETH', 'THB_USDT']  # เหรียญที่ต้องการเทรด
MIN_PROFIT_PERCENT = 0.5  # กำไรขั้นต่ำ 0.5%
MAX_TRADE_AMOUNT = 1000  # จำนวนเงินสูงสุดต่อออเดอร์ (THB)

# Backup Settings
BACKUP_DIR = 'backups'
BACKUP_RETENTION_DAYS = 30
