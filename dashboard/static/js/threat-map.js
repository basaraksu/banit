// --- HARİTA MODÜLÜ ---
let map;
let markersLayer = new L.LayerGroup();

// Botların en çok geldiği ülkelerin ortalama koordinatları (Enlem, Boylam)
// Eğer sistemine yeni bir ülkeden saldırı gelirse ve haritada çıkmazsa buraya ekleyebilirsin.
const countryCoords = {
    'TR': [38.96, 35.24], 'US': [37.09, -95.71], 'CN': [35.86, 104.19],
    'RU': [61.52, 105.31], 'NL': [52.13, 5.29],   'DE': [51.16, 10.45],
    'GB': [55.37, -3.43], 'FR': [46.22, 2.21],   'IN': [20.59, 78.96],
    'BR': [-14.23, -51.92],'UA': [48.37, 31.16],  'VN': [14.05, 108.27]
};

function initMap() {
    // Haritayı oluştur (Başlangıç noktası: Avrupa/Ortadoğu)
    map = L.map('threat-map').setView([35.0, 15.0], 2);

    // Karanlık (Cyber) Tema Harita Katmanı (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CartoDB',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    markersLayer.addTo(map);
}

function updateMap(logs) {
    markersLayer.clearLayers(); // Eski noktaları temizle
    
    // Ülkelere göre saldırı sayılarını grupla
    let attackCounts = {};
    logs.forEach(log => {
        let cc = log.country ? log.country.toUpperCase() : null;
        if (cc && countryCoords[cc]) {
            attackCounts[cc] = (attackCounts[cc] || 0) + 1;
        }
    });

    // Haritaya kırmızı çemberleri ekle
    for (let cc in attackCounts) {
        let count = attackCounts[cc];
        let coords = countryCoords[cc];
        
        // Saldırı sayısı arttıkça çember büyüsün
        let radius = Math.min(count * 50000 + 100000, 1000000); 

        let circle = L.circle(coords, {
            color: '#ff416c',
            fillColor: '#ff4b2b',
            fillOpacity: 0.5,
            radius: radius
        });

        circle.bindPopup(`<b>${cc}</b><br>${count} Saldırı Girişimi`);
        markersLayer.addLayer(circle);
    }
}

export { initMap, updateMap };