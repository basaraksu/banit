#!/bin/bash

# 1. Veritabanı klasörü yoksa oluştur (Docker volume için lazım olacak)
mkdir -p /app/database

echo "[*] Banit Avcı Motoru (Honeypot) Başlatılıyor..."
# honeypot.py engine klasörünün içinde olduğu için yolu böyle veriyoruz:
python engine/honeypot.py & 

echo "[*] Banit Kontrol Paneli (API) Başlatılıyor..."
uvicorn api.main:app --host 0.0.0.0 --port 8000