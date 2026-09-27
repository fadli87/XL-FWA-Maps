# 🗺️ XL SATU Maps - Coverage, Homepass & BTS Tower (Kabupaten Cilacap)

Aplikasi Web Map interaktif, responsif, dan ringan berbasis **Leaflet.js** yang dirancang khusus untuk tim *Sales Field* XL SATU di Kabupaten Cilacap.

---

## 🚀 Fitur Utama
- **380 Titik Tower BTS XL**: Lengkap dengan Site Name, Tower ID, eNodeB ID, Antenna Height, SPV, dan warna status asli KMZ.
- **607.242 Titik Homepass / Building**: Target prospek rumah pelanggan dengan ID bangunan, status prioritas kunjungan, dan tipe jaringan.
- **250.835 Poligon Coverage Area**: Visualisasi poligon area jangkauan jaringan (Indoor-Outdoor & Outdoor).
- **Pemuatan On-Demand Per Kecamatan**: Ringan dibuka di HP dengan *zero lag* (GPU Canvas Acceleration).
- **Live GPS Tracker**: Deteksi lokasi akurat tim sales di lapangan.
- **Pencarian Real-Time**: Cari ID Bangunan, Desa, Kecamatan, Cluster, atau Nama Tower.

---

## 📁 Struktur Folder
```text
├── data/
│   ├── raw_coverage/     # 89 file KMZ coverage per kecamatan & desa
│   └── raw_tower/        # File KMZ Tower BTS XL Cilacap
├── public/               # File website statis & GeoJSON
│   ├── index.html        # Main web map viewer
│   ├── districts.json    # Indeks metadata kecamatan
│   ├── tower.geojson     # Data titik Tower BTS
│   ├── coverage/         # GeoJSON coverage per kecamatan
│   └── buildings/        # GeoJSON homepass target per kecamatan
├── scripts/
│   └── process_data.py   # Script otomatisasi ekstraksi KMZ -> GeoJSON
└── requirements.txt      # Dependensi Python
```

---

## 🛠️ Menjalankan Secara Lokal
1. Jalankan web server:
   ```bash
   python -m http.server 8000 --directory public
   ```
2. Buka browser di [http://localhost:8000](http://localhost:8000).
