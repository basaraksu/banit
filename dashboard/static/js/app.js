// banit/dashboard/static/js/app.js

import { initMap, updateMap } from './threat-map.js';

// Helper Fonksiyonlar
async function refreshLogs() {
    try {
        const response = await fetch('/api/logs');
        if (!response.ok) throw new Error('Network response was not ok');

        const logs = await response.json();
        updateMap(logs); // Yeni loglara göre haritayı güncelle
        const tbody = document.querySelector('tbody');

        // Tabloyu güncelle (Yeni sütunlar eklendi: log.country ve log.risk)
        tbody.innerHTML = logs.map(log => {
            let riskColor = '#28a745';
            if (log.risk > 50) riskColor = '#ffc107';
            if (log.risk > 80) riskColor = '#dc3545';

            // Ülke kodunu küçük harfe çevirip CSS sınıfı oluşturuyoruz
            let countryCode = log.country ? log.country.toLowerCase() : '';
            // Eğer ülke kodu yoksa veya '-' ise bir dünya ikonu veya boşluk göster
            let flagHtml = countryCode && countryCode !== '-'
                ? `<span class="fi fi-${countryCode}" style="font-size: 1.5em; border-radius: 2px;"></span>`
                : `<span>?</span>`;

            return `
                <tr>
                    <td>${log.time}</td>
                    <td>
                        <div class="d-flex align-items-center justify-content-start gap-2">
                            ${flagHtml} 
                            <small class="text-uppercase">${log.country || ''}</small>
                        </div>
                    </td>
                    <td><span class="badge bg-danger">${log.ip}</span></td>
                    <td>${log.user}</td>
                    <td>${log.pwd}</td>
                    <td>
                        <span class="badge" style="background-color: ${riskColor}; color: white;">
                            ${log.risk || 0}
                        </span>
                    </td>
                    <td>
                        ${log.status === 1
                    ? '<span class="badge bg-success shadow-sm">BANLANDI</span>'
                    : '<span class="badge bg-warning text-dark">İzlendi</span>'}
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error("Güncelleme hatası:", err);
    }
}

async function updateStats() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();

        // Toplam saldırı sayısını güncelle
        const totalAttacks = document.getElementById('total-attacks');
        if (totalAttacks) totalAttacks.innerText = stats.total_attacks;

        document.getElementById('top-ip').innerText = stats.top_ip;
        document.getElementById('top-ip-count').innerText = `${stats.top_ip_count} deneme`;

        document.getElementById('top-user').innerText = stats.top_user;
        document.getElementById('top-user-count').innerText = `${stats.top_user_count} deneme`;
    } catch (err) {
        console.error("Stats güncelleme hatası:", err);
    }
}

async function updateDashboard() {
    await refreshLogs();  // Tabloyu günceller
    await updateStats();  // Üstteki 3 kartı günceller
}

// window.logout diyerek fonksiyonu tüm HTML sayfasına açıyoruz
window.logout = function() {
    // Çerezin tarihini geçmişe alarak tarayıcının onu silmesini sağla
    document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    // Login sayfasına yönlendir
    window.location.href = '/login';
};

// Zamanlayıcı Ayarları
const totalTime = 10;
let timeLeft = totalTime;

// Sayfa ilk yüklendiğinde çalışacak kısım
document.addEventListener('DOMContentLoaded', () => {
    // haritayı oluştur
    initMap();
    
    // 1. Hemen verileri çek (Sayfa açılır açılmaz)
    updateDashboard();

    // 2. Zamanlayıcıyı başlat (Sadece bir tane setInterval yeterli)
    setInterval(() => {
        timeLeft--;
        if (timeLeft <= 0) {
            updateDashboard(); // Sayfayı yenilemeden verileri tazele
            timeLeft = totalTime; // Timer'ı sıfırla
        }
    }, 1000);
});