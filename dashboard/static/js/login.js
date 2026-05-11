document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault(); // Sayfanın yenilenmesini engelle
    
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-msg');

    try {
        // Backend'e şifreyi sor
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });

        if (response.ok) {
            const data = await response.json();
            
            // GELEN TOKEN'I ÇEREZE (COOKIE) KAYDET (Backend buradan okuyacak)
            // max-age=86400 demek 1 gün (24 saat) boyunca sistemde kal demek
            document.cookie = `access_token=${data.access_token}; path=/; max-age=86400; SameSite=Strict`; 
            
            // Başarılıysa anasayfaya (Haritaya) fırlat
            window.location.href = '/'; 
        } else {
            // Şifre yanlışsa
            errorMsg.textContent = '[!] Erişim Reddedildi: Yetkisiz Giriş.';
            errorMsg.classList.remove('d-none');
        }
    } catch (error) {
        errorMsg.textContent = '[!] Sunucu bağlantı hatası.';
        errorMsg.classList.remove('d-none');
    }
});