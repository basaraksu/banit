import sqlite3
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
    
    # Eğer settings tablosu boşsa, varsayılan ayarları (Key-Value) ekle
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        default_settings = [
            ('telegram_token', ''),
            ('telegram_chat_id', ''),
            ('telegram_enabled', '0'),
            ('autoban_enabled', '0'),
            ('autoban_threshold', '2')
        ]
        cursor.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", default_settings)

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


def get_guardian_settings():
    """Guardian (Oto-ban) ayarlarını veritabanından çeker."""
    conn = get_connection() # Senin db dosyasında yazdığın bağlantı fonksiyonu
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings WHERE key IN ('autoban_enabled', 'autoban_threshold')")
    settings = dict(cursor.fetchall())
    conn.close()
    
    return {
        "autoban_enabled": settings.get("autoban_enabled") == "1",
        "threshold": int(settings.get("autoban_threshold", 2))
    }

def get_ip_attempt_count(ip_address):
    """Bir IP adresinin bugüne kadar kaç kez hatalı giriş yaptığını sayar."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ssh_logs WHERE ip_address = ?", (ip_address,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def is_ip_already_banned(ip_address):
    """Bu IP daha önce banlanmış mı diye kontrol eder (Çifte ban atmamak için)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned FROM ssh_logs WHERE ip_address = ? LIMIT 1", (ip_address,))
    row = cursor.fetchone()
    conn.close()
    return row and row[0] == 1

def set_ip_banned(ip_address):
    """Başarıyla banlanan IP'nin veritabanındaki durumunu 1 (Banlı) yapar."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE ssh_logs SET is_banned = 1 WHERE ip_address = ?", (ip_address,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()