import requests
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
import subprocess
import os
import config
from database import Database

class BitkubBot:
    def __init__(self):
        self.db = Database()
        self.last_prices = {}
    
    def get_ticker(self):
        """ดึงราคาปัจจุบัน"""
        try:
            response = requests.get(f'{config.BITKUB_API_URL}/api/market/ticker')
            return response.json()
        except Exception as e:
            print(f"Error getting ticker: {e}")
            return None
    
    def save_prices(self):
        """บันทึกราคาทุก 1 ชั่วโมง"""
        ticker = self.get_ticker()
        if ticker:
            for symbol in config.SYMBOLS:
                if symbol in ticker:
                    price = ticker[symbol]['last']
                    self.db.save_price(symbol, price)
                    self.last_prices[symbol] = price
                    print(f"✅ Saved {symbol}: {price} THB")
        return ticker is not None
    
    def analyze_market(self):
        """วิเคราะห์ตลาดและหาโอกาสเทรด"""
        signals = []
        for symbol in config.SYMBOLS:
            prices = self.db.get_prices(symbol, hours=24)
            if len(prices) < 2:
                continue
            
            current_price = prices[0]['price']
            avg_24h = sum([p['price'] for p in prices]) / len(prices)
            
            # Simple strategy: ซื้อถ้าราคาต่ำกว่าค่าเฉลี่ย, ขายถ้าสูงกว่า
            change_percent = ((current_price - avg_24h) / avg_24h) * 100
            
            if change_percent < -config.MIN_PROFIT_PERCENT:
                signals.append({
                    'symbol': symbol,
                    'action': 'BUY',
                    'price': current_price,
                    'reason': f'ราคาต่ำกว่าเฉลี่ย {abs(change_percent):.2f}%'
                })
            elif change_percent > config.MIN_PROFIT_PERCENT:
                signals.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'price': current_price,
                    'reason': f'ราคาสูงกว่าเฉลี่ย {change_percent:.2f}%'
                })
        
        return signals
    
    def execute_trade(self, signal):
        """จำลองการเทรด (ในการใช้จริงให้เรียก Bitkub API)"""
        # คำนวณกำไร/ขาดทุน
        amount = config.MAX_TRADE_AMOUNT / signal['price']
        profit = amount * signal['price'] * (config.MIN_PROFIT_PERCENT / 100)
        
        if signal['action'] == 'SELL':
            self.db.save_trade(signal['symbol'], 'SELL', signal['price'], amount, profit)
            print(f"🟢 SELL {signal['symbol']} @ {signal['price']} THB | Profit: {profit:.2f} THB")
        else:
            self.db.save_trade(signal['symbol'], 'BUY', signal['price'], amount, -profit)
            print(f"🔵 BUY {signal['symbol']} @ {signal['price']} THB")
    
    def health_check(self):
        """ตรวจสุขภาพระบบ"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'database': 'OK',
            'api': 'OK'
        }
        
        try:
            self.db.cursor.execute("SELECT 1")
        except:
            status['database'] = 'ERROR'
        
        if not self.get_ticker():
            status['api'] = 'ERROR'
        
        print(f"💚 Health Check: DB={status['database']}, API={status['api']}")
        return status
    
    def generate_daily_report(self):
        """สร้างรายงานประจำวัน"""
        trades = self.db.get_trades_today()
        if not trades:
            print("📊 No trades today")
            return
        
        total_profit = sum([t['profit'] for t in trades])
        success = sum([1 for t in trades if t['profit'] > 0])
        success_rate = (success / len(trades)) * 100
        
        self.db.save_daily_report(
            datetime.now().date(),
            len(trades),
            total_profit,
            success_rate
        )
        
        print(f"\n📊 รายงานวันนี้ ({datetime.now().date()})")
        print(f"   จำนวนเทรด: {len(trades)}")
        print(f"   กำไร/ขาดทุน: {total_profit:.2f} THB")
        print(f"   อัตราความสำเร็จ: {success_rate:.1f}%\n")
    
    def backup_database(self):
        """สำรองฐานข้อมูล"""
        os.makedirs(config.BACKUP_DIR, exist_ok=True)
        backup_file = f"{config.BACKUP_DIR}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        cmd = f"mysqldump -h {config.DB_HOST} -u {config.DB_USER} -p{config.DB_PASSWORD} {config.DB_NAME} > {backup_file}"
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"💾 Backup saved: {backup_file}")
            
            # ลบ backup เก่า
            for f in os.listdir(config.BACKUP_DIR):
                file_path = os.path.join(config.BACKUP_DIR, f)
                if os.path.getmtime(file_path) < time.time() - (config.BACKUP_RETENTION_DAYS * 86400):
                    os.remove(file_path)
        except Exception as e:
            print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    import sys
    bot = BitkubBot()
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "save_prices":
            bot.save_prices()
        elif action == "health_check":
            bot.health_check()
        elif action == "daily_report":
            bot.generate_daily_report()
        elif action == "backup":
            bot.backup_database()
        elif action == "trade":
            signals = bot.analyze_market()
            for signal in signals:
                bot.execute_trade(signal)
    else:
        print("Usage: python bot.py [save_prices|health_check|daily_report|backup|trade]")
