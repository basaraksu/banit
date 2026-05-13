# Temel işletim sistemi olarak hafif bir Python sürümü seçiyoruz
FROM python:3.10-slim

# EN KRİTİK ADIM: Konteyner içine iptables ve sudo kuruyoruz
# Çünkü python motorumuz (engine.py) "sudo iptables" komutları çalıştırıyor
RUN apt-get update && apt-get install -y iptables sudo && rm -rf /var/lib/apt/lists/*

# İçerideki çalışma klasörümüz /app olacak
WORKDIR /app

# Önce kütüphane listesini kopyala ve kur (Önbellek optimizasyonu için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Şimdi projenin geri kalan tüm dosyalarını kopyala
COPY . .

# Başlatıcı script'e çalışma yetkisi ver (Garantiye alıyoruz)
RUN chmod +x start.sh

# Konteyner ayağa kalktığında bu dosyayı ateşle
CMD ["./start.sh"]