import socket
import paramiko
import threading
import os
import sys

import logging
# Paramiko'nun sadece KRİTİK hataları yazmasını sağla, ufak tefek şeyleri sustur
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

# Veritabanı yöneticisini içe aktarabilmek için path ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import add_ssh_log

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

if __name__ == "__main__":
    start_engine()