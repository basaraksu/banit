# banit/core/intelligence.py
import requests
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "banit_logs.db")
# API Anahtarını buraya yapıştır veya çevre değişkeninden (env) al
ABUSE_IPDB_KEY = "3a130605cd44a5dc2628ab57ee4c98ba867afa9964e3f9efdc6ce0fac2b0687a1c8f4e044b770c04"

def check_ip_intelligence(ip_address):
    """
    Önce veritabanına bakar, bulamazsa AbuseIPDB'den çeker ve kaydeder.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Önce kendi veritabanımızda (önbellekte) var mı diye bak (Daha önce kaydedilmişse)
    cursor.execute("""
        SELECT country_code, risk_score 
        FROM ssh_logs 
        WHERE ip_address = ? AND country_code != '-' 
        LIMIT 1
    """, (ip_address,))
    
    cached_result = cursor.fetchone()
    
    if cached_result:
        conn.close()
        return {"countryCode": cached_result[0], "abuseConfidenceScore": cached_result[1]}

    # 2. Veritabanında yoksa AbuseIPDB'ye sor
    url = 'https://api.abuseipdb.com/api/v2/check'
    querystring = {
        'ipAddress': ip_address,
        'maxAgeInDays': '90'
    }
    headers = {
        'Accept': 'application/json',
        'Key': ABUSE_IPDB_KEY
    }

    try:
        response = requests.request(method='GET', url=url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()['data']
            result = {
                "countryCode": data.get('countryCode', '-'),
                "abuseConfidenceScore": data.get('abuseConfidenceScore', 0)
            }
        else:
            print(f"[*] AbuseIPDB Hatası: {response.status_code}")
            result = {"countryCode": "-", "abuseConfidenceScore": 0}
    except Exception as e:
        print(f"[*] İstihbarat çekilirken hata: {e}")
        result = {"countryCode": "-", "abuseConfidenceScore": 0}

    conn.close()
    return result