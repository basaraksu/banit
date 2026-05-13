🛡️ BANIT - Akıllı SSH Honeypot & IPS
=====================================

Banit, sunucunuza gelen SSH saldırılarını yakalayan, analiz eden ve saldırganları otomatik olarak engelleyen (banlayan) bir güvenlik sistemidir.

⚠️ Önemli Hazırlık
------------------

Banit, saldırganları yakalamak için **22** portunu kullanacaktır. Kuruluma başlamadan önce sunucunuzun asıl SSH portunu (örneğin **4445**'e) değiştirdiğinizden ve bu portun güvenlik duvarınızda açık olduğundan emin olun.

🚀 Kurulum (5 Dakikada)
-----------------------

### 1\. Dosyaları İndirin

Bash

`   git clone https://github.com/basaraksu/banit.git  cd banit   `

### 2\. Ayarları Yapın

Sistemdeki örnek ayar dosyasını kopyalayın ve kendinize göre düzenleyin:

Bash

`   cp .env.example .env  nano .env   `

_(Burada ADMIN\_USERNAME ve ADMIN\_PASSWORD kısımlarını belirleyin.)._

### 3\. Sistemi Başlatın (Docker)

Sistemi tek bir paket olarak ayağa kaldırın:

Bash

`   docker-compose up --build -d   `

### 4\. Tuzak Kapısını Açın

Dışarıdan 22 portuna gelenleri Banit'e yönlendirmek için bu komutu çalıştırın:

Bash

`   sudo iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port 2222   `

📊 Paneli Görüntüleme
---------------------

Banit paneli güvenlik nedeniyle dış dünyaya kapalıdır. Panele erişmek için kendi bilgisayarınızdan bir **SSH Tüneli** açmalısınız:

**Kendi bilgisayarınızda (Terminal/CMD):**

Bash

`   ssh -L 8000:localhost:8000 kullanici_adi@sunucu_ip_adresi -p 4445   `

Bağlantı sağlandıktan sonra tarayıcınızdan şu adrese girin:👉 **http://localhost:8000**

🛠️ Temel Komutlar
------------------

*   **Logları İzle:** docker-compose logs -f
    
*   **Sistemi Durdur:** docker-compose down
    
*   **Banlı IP'leri Gör:** sudo iptables -L BANIT\_JAIL -n
    

### Özellikler

*   ✅ **Otomatik Ban:** Belirlediğiniz sınıra ulaşan IP anında engellenir.
    
*   ✅ **Telegram Bildirimi:** Saldırgan banlandığı an cebinize mesaj gelir.
    
*   ✅ **Harita Desteği:** Saldırıların hangi ülkeden geldiğini görsel olarak izleyin.
    
*   ✅ **Hafif Mimari:** Docker sayesinde sunucunuzu yormadan çalışır.