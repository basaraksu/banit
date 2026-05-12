document.addEventListener('DOMContentLoaded', async () => {
    // Sayfa açıldığında mevcut ayarları veritabanından çekip kutulara doldur
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('telegram_token').value = data.telegram_token || '';
            document.getElementById('telegram_chat_id').value = data.telegram_chat_id || '';
            document.getElementById('telegram_enabled').checked = data.telegram_enabled;
            document.getElementById('autoban_enabled').checked = data.autoban_enabled;
            document.getElementById('autoban_threshold').value = data.autoban_threshold || 2;
        }
    } catch (error) {
        showAlert('Ayarlar yüklenirken sunucuya ulaşılamadı.', 'danger');
    }
});

// Kaydet butonuna basıldığında ayarları API'ye gönder
document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
        telegram_token: document.getElementById('telegram_token').value,
        telegram_chat_id: document.getElementById('telegram_chat_id').value,
        telegram_enabled: document.getElementById('telegram_enabled').checked,
        autoban_enabled: document.getElementById('autoban_enabled').checked,
        autoban_threshold: parseInt(document.getElementById('autoban_threshold').value)
    };

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showAlert('[+] Sistem ayarları başarıyla çekirdeğe yazıldı.', 'success');
        } else {
            showAlert('[-] Ayarlar kaydedilemedi (Yetkisiz veya Hatalı Veri).', 'danger');
        }
    } catch (error) {
        showAlert('[-] Sunucu bağlantı hatası.', 'danger');
    }
});

// Ekrana havalı mesaj basma fonksiyonu
function showAlert(message, type) {
    const alertBox = document.getElementById('alert-box');
    alertBox.className = `alert alert-${type} mt-3`; // Rengi belirle (yeşil/kırmızı)
    alertBox.textContent = message;
    alertBox.classList.remove('d-none');
    
    // 3 saniye sonra mesajı gizle
    setTimeout(() => { alertBox.classList.add('d-none'); }, 3000);
}