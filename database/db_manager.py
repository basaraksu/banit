import sqlite3
import os
from core.intelligence import check_ip_intelligence

DB_PATH = os.path.join(os.path.dirname(__file__), 'banit_logs.db')

def get_connection():
    """Veritabanı bağlantısı sağlar."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Tabloları ilk kez oluşturur."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Saldırı Logları Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ssh_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            username TEXT,
            password TEXT,
            is_banned INTEGER DEFAULT 0,
            country_code TEXT,
            risk_score INTEGER DEFAULT 0
        )
    ''')
    
    # Banlı IP'ler ve Kurallar Tablosu (Arayüzden yöneteceğimiz kısım)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ban_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE,
            reason TEXT,
            ban_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            expiry_date DATETIME
        )
    ''')
    
    # Ayarlar Tablosu (Telegram vb.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("[DB] Veritabanı ve tablolar başarıyla hazırlandı.")
    
    
def add_ssh_log(ip_address, username, password):
    """Saldırı verisini veritabanına kaydeder."""
    # AbuseIPDB'den veya yerel cache'den veriyi al
    intel = check_ip_intelligence(ip_address)
    country = intel['countryCode']
    risk = intel['abuseConfidenceScore']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # SQL sorgunu yeni kolonları içerecek şekilde güncelle
    cursor.execute("""
        INSERT INTO ssh_logs (ip_address, username, password, is_banned, country_code, risk_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ip_address, username, password, 0, country, risk))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()