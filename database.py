import mysql.connector
from datetime import datetime
import config

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            DB_PORT=config.DB_PORT,
            database=config.DB_NAME
        )
        self.cursor = self.conn.cursor(dictionary=True)
        self.init_tables()
    
    def init_tables(self):
        # ตารางเก็บราคา
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20),
                price DECIMAL(20,8),
                timestamp DATETIME,
                INDEX idx_symbol_time (symbol, timestamp)
            )
        ''')
        
        # ตารางเก็บการเทรด
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20),
                side VARCHAR(10),
                price DECIMAL(20,8),
                amount DECIMAL(20,8),
                profit DECIMAL(20,8),
                timestamp DATETIME,
                status VARCHAR(20)
            )
        ''')
        
        # ตารางรายงานประจำวัน
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE UNIQUE,
                total_trades INT,
                profit DECIMAL(20,8),
                success_rate DECIMAL(5,2),
                created_at DATETIME
            )
        ''')
        self.conn.commit()
    
    def save_price(self, symbol, price):
        sql = "INSERT INTO prices (symbol, price, timestamp) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (symbol, price, datetime.now()))
        self.conn.commit()
    
    def save_trade(self, symbol, side, price, amount, profit):
        sql = '''INSERT INTO trades (symbol, side, price, amount, profit, timestamp, status) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)'''
        self.cursor.execute(sql, (symbol, side, price, amount, profit, datetime.now(), 'completed'))
        self.conn.commit()
    
    def get_prices(self, symbol, hours=24):
        sql = '''SELECT * FROM prices 
                 WHERE symbol = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                 ORDER BY timestamp DESC'''
        self.cursor.execute(sql, (symbol, hours))
        return self.cursor.fetchall()
    
    def get_trades_today(self):
        sql = "SELECT * FROM trades WHERE DATE(timestamp) = CURDATE() ORDER BY timestamp DESC"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def get_daily_summary(self, days=30):
        sql = '''SELECT DATE(timestamp) as date, 
                        COUNT(*) as trades,
                        SUM(profit) as profit,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                 FROM trades 
                 WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                 GROUP BY DATE(timestamp)
                 ORDER BY date DESC'''
        self.cursor.execute(sql, (days,))
        return self.cursor.fetchall()
    
    def save_daily_report(self, date, trades, profit, success_rate):
        sql = '''INSERT INTO daily_reports (date, total_trades, profit, success_rate, created_at)
                 VALUES (%s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE 
                 total_trades=%s, profit=%s, success_rate=%s'''
        now = datetime.now()
        self.cursor.execute(sql, (date, trades, profit, success_rate, now, trades, profit, success_rate))
        self.conn.commit()
    
    def close(self):
        self.cursor.close()
        self.conn.close()
