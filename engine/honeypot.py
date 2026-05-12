import socket
import paramiko
import threading
import os
import sys
import subprocess
import threading

import logging
# Paramiko'nun sadece KRİTİK hataları yazmasını sağla, ufak tefek şeyleri sustur
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

# Veritabanı yöneticisini içe aktarabilmek için path ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import add_ssh_log, get_guardian_settings, get_ip_attempt_count, is_ip_already_banned, set_ip_banned
from core.telegram_bot import send_telegram_alert, start_ping_listener

# Anahtarın yolunu belirle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOST_KEY = paramiko.RSAKey(filename=os.path.join(BASE_DIR, 'server.key'))


class BanitSSHServer(paramiko.ServerInterface):
    def __init__(self, client_ip):
        self.client_ip = client_ip

    def check_auth_password(self, username, password):
        # Saldırganın IP ve şifresini yakala
        print(f"\n[!!!] SALDIRI TESPİT EDİLDİ!")
        print(f"    IP      : {self.client_ip}")
        print(f"    Kullanıcı: {username}")
        print(f"    Şifre   : {password}")
        print("-" * 30)
        # Veritabanına log ekle
        add_ssh_log(self.client_ip, username, password)
        process_guardian_actions(self.client_ip, username, password)
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

def handle_client(client_socket, client_addr):
    # IP adresini tuple'dan çıkarıp bir değişkene atayalım
    ip_address = client_addr[0]
    
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        server = BanitSSHServer(ip_address)
        transport.start_server(server=server)
        channel = transport.accept(20)
        
    except paramiko.ssh_exception.SSHException:
        print(f"[*] Port Tarayıcı Tespit Edildi (Banner Yok): {ip_address}")
        return  
        
    except EOFError:
        print(f"[*] Bağlantı aniden koptu: {ip_address}")
        return
        
    except socket.timeout:
        print(f"[*] Bağlantı zaman aşımına uğradı: {ip_address}")
        return
        
    except Exception as e:
        print(f"[*] İstemci işlenirken hata ({ip_address}): {e}")
        return

def start_engine(port=2222):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(100)
    print(f"[*] Banit SSH Motoru Dinliyor... Port: {port}")
    
    while True:
        client_socket, client_addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, client_addr)).start()


def process_guardian_actions(ip_address, username, password):
    """Ayarları okur, limiti kontrol eder, telegrama yazar ve gerekirse banlar."""
    
    # 1. AYARLARI ÇEK (Tertemiz, SQL yok)
    settings = get_guardian_settings()
    
    # 2. BU IP BUGÜNE KADAR KAÇ KERE DENEMİŞ?
    attempts = get_ip_attempt_count(ip_address)

    # 3. STANDART TELEGRAM BİLDİRİMİ (Ping)
    alert_msg = f"⚠️ <b>[BANIT] Yeni Sızıntı Denemesi</b>\nIP: <code>{ip_address}</code>\nKullanıcı: {username}\nŞifre: {password}\nDeneme: {attempts}/{settings['threshold']}"
    send_telegram_alert(alert_msg)

    # 4. İNFAZ AŞAMASI (Auto-Ban)
    if settings['autoban_enabled'] and attempts >= settings['threshold']:
        
        # IP zaten daha önceden banlanmamışsa işlem yap
        if not is_ip_already_banned(ip_address):
            print(f"[GUARDIAN] {ip_address} kırmızı çizgiyi aştı! Banlanıyor...")
            
            try:
                # Linux iptables ile adamın IP'sini tamamen engelle
                subprocess.run(["sudo", "iptables", "-A", "BANIT_JAIL", "-s", ip_address, "-j", "DROP"], check=True)
                
                # Veritabanında is_banned değerini 1 (True) yap
                set_ip_banned(ip_address)
                
                # Zafer mesajını Telegram'a at
                ban_msg = f"🔨 <b>[GUARDIAN] DÜŞMAN İMHA EDİLDİ!</b>\nHedef IP: <code>{ip_address}</code>\nSebep: {settings['threshold']} hatalı deneme sınırı aşıldı.\nAksiyon: iptables DROP"
                send_telegram_alert(ban_msg)
                
            except subprocess.CalledProcessError as e:
                print(f"[!] Banlama başarısız (Sudo yetkisi gerekebilir): {e}")

def init_firewall():
    """Banit için izole bir iptables zinciri (hapishane) kurar."""
    try:
        # Önce 'BANIT_JAIL' adında bir zincir var mı diye sessizce kontrol et
        subprocess.run(["sudo", "iptables", "-L", "BANIT_JAIL"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Hata vermediyse zaten vardır, bir şey yapma
    except subprocess.CalledProcessError:
        # Hata verdiyse zincir yoktur, hemen inşa edelim:
        print("[FIREWALL] BANIT_JAIL (İzole Hapishane) inşa ediliyor...")
        
        # 1. BANIT_JAIL adında yeni bir alt zincir oluştur
        subprocess.run(["sudo", "iptables", "-N", "BANIT_JAIL"])
        
        # 2. Ana kapıdan (INPUT) giren herkesi önce bu hapishaneden geçir
        subprocess.run(["sudo", "iptables", "-I", "INPUT", "-j", "BANIT_JAIL"])
        print("[FIREWALL] Hapishane hazır. Tüm trafik buradan süzülecek.")

if __name__ == "__main__":
    init_firewall()  # Firewall'u başlat (Sadece ilk seferde çalışır, sonra var mı diye bakar)
    
    threading.Thread(target=start_ping_listener, daemon=True).start()
    start_engine()