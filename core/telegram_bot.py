import requests
import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'banit_logs.db')
# Eğer DB_PATH hata verirse, kendi sistemine göre yolu (Örn: 'banit_logs.db') ayarlayabilirsin.

def get_telegram_settings():
    """Veritabanından güncel Telegram ayarlarını çeker."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings WHERE key IN ('telegram_token', 'telegram_chat_id', 'telegram_enabled')")
        settings = dict(cursor.fetchall())
        conn.close()
        
        return {
            "token": settings.get("telegram_token", ""),
            "chat_id": settings.get("telegram_chat_id", ""),
            "enabled": settings.get("telegram_enabled") == "1"
        }
    except Exception as e:
        print(f"[!] Telegram ayarları okunamadı: {e}")
        return {"enabled": False}

def send_telegram_alert(message):
    """Eğer ayarlar açıksa Telegram üzerinden bildirim gönderir."""
    settings = get_telegram_settings()
    
    # Eğer bot kapalıysa veya bilgiler eksikse hiçbir şey yapma
    if not settings["enabled"] or not settings["token"] or not settings["chat_id"]:
        return False
        
    url = f"https://api.telegram.org/bot{settings['token']}/sendMessage"
    payload = {
        "chat_id": settings["chat_id"],
        "text": message,
        "parse_mode": "HTML" # Mesajlarda kalın/italik yazı kullanabilmek için
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"[!] Telegram hatası: {response.text}")
            return False
    except Exception as e:
        print(f"[!] Telegram bağlantı hatası: {e}")
        return False


def get_quick_stats():
    """Ping atıldığında durum raporu vermek için hızlıca veritabanına bakar."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ssh_logs")
        total_attacks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ssh_logs WHERE is_banned = 1")
        banned_ips = cursor.fetchone()[0]
        conn.close()
        return total_attacks, banned_ips
    except:
        return 0, 0

def start_ping_listener():
    """Arka planda sessizce çalışıp Telegram'dan gelen mesajları dinler."""
    last_update_id = 0
    print("[*] Telegram Ping-Pong İstihbarat Ağı Dinlemede...")
    
    while True:
        try:
            settings = get_telegram_settings()
            # Bot kapalıysa veya bilgiler eksikse 10 saniye uyu ve tekrar kontrol et
            if not settings["enabled"] or not settings["token"] or not settings["chat_id"]:
                time.sleep(10)
                continue
                
            url = f"https://api.telegram.org/bot{settings['token']}/getUpdates"
            # timeout=20 ile Telegram'a "Mesaj yoksa 20 saniye bekle, öyle cevap dön" diyoruz (Long Polling)
            params = {"offset": last_update_id, "timeout": 20} 
            
            response = requests.get(url, params=params, timeout=25)
            data = response.json()
            
            if data.get("ok"):
                for update in data["result"]:
                    last_update_id = update["update_id"] + 1
                    
                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id", ""))
                    text = message.get("text", "").strip().lower()
                    
                    # SİHİRLİ KALKAN BURADA BAŞLIYOR:
                    msg_date = message.get("date", 0) # Mesajın atıldığı saniye (Unix time)
                    
                    # Eğer mesajın üzerinden 60 saniyeden fazla zaman geçmişse atla (continue)
                    if time.time() - msg_date > 60:
                        print(f"[*] Bayat mesaj atlandı: {text}")
                        continue
                    
                    # GÜVENLİK: Sadece senin Chat ID'nden gelen mesajlara cevap ver! (Başkası botu bulsa da konuşamaz)
                    if chat_id == settings["chat_id"]:
                        if text in ["ping", "durum", "/status", "selam", "hey"]:
                            # İstatistikleri çek
                            total, banned = get_quick_stats()
                            
                            # Raporu gönder
                            msg = (f"🟢 <b>[BANIT AKTİF]</b>\n"
                                   f"Sistem ayakta, motorlar çalışıyor!\n\n"
                                   f"🛡️ <b>Toplam Saldırı:</b> {total}\n"
                                   f"🔨 <b>Banlanan IP:</b> {banned}\n\n"
                                   f"<i>Nöbet devam ediyor...</i>")
                            send_telegram_alert(msg)
        except Exception as e:
            # İnternet kopsa veya Telegram çökse bile döngü kırılmasın
            time.sleep(5)
            
        time.sleep(1) # CPU'yu yormamak için çok kısa bir mola


# Dosyayı tek başına çalıştırıp test etmek için:
if __name__ == "__main__":
    print("Telegram testi başlatılıyor...")
    success = send_telegram_alert("🛡️ <b>[BANIT SİSTEM TESTİ]</b>\nSistem başarıyla Telegram ağına bağlandı. Nöbet başlıyor!")
    if success:
        print("Test mesajı başarıyla gönderildi! Telefonunu kontrol et.")
    else:
        print("Mesaj gönderilemedi. Lütfen Token ve Chat ID'yi kontrol et.")