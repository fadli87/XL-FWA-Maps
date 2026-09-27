# Implementation Plan: Web Map Coverage & BTS Cilacap (Optimized for Mobile Sales)

## 1. Project Context & Objectives
Membangun web map interaktif satu halaman (Single Page Application) yang sangat ringan untuk digunakan oleh tim sales di lapangan melalui *browser* HP. Peta ini akan menampilkan area *coverage* (berasal dari 89 file KMZ) dan titik Tower BTS (berasal dari 1 file KMZ).

**Kendala Utama & Solusi:**
- Data awal sangat besar (~960.000 fitur/titik), menyebabkan *lag* jika dirender mentah di HP.
- Solusi: Ekstraksi *backend* menggunakan Python (`geopandas`) untuk membuang tabel atribut HTML yang berat, melakukan *simplify polygon* tingkat tinggi pada area *coverage*, dan merender titik Tower BTS menggunakan `Leaflet.markercluster` di *frontend*.

## 2. Directory Structure
Buat struktur direktori berikut di dalam *workspace*:
```text
/
├── data/
│   ├── raw_coverage/     # Letakkan 89 file KMZ (3301_1.kmz dst) di sini
│   └── raw_tower/        # Letakkan file Tower_BTS_XL_Cilacap.kmz di sini
├── public/               # Direktori output untuk web statis
│   ├── index.html        # Main web viewer
│   └── (file geojson hasil generate akan tersimpan di sini)
├── scripts/
│   └── process_data.py   # Script ekstraksi dan kompresi spasial
├── requirements.txt      # Dependensi Python
└── implementation_plan.md

3. Step-by-Step Execution Tasks
Task 1: Setup Environment (Python)
Buat virtual environment Python di terminal.

Buat file requirements.txt dengan isi:

Plaintext
geopandas==0.14.3
fiona==1.9.5
pandas==2.2.1
Jalankan pip install -r requirements.txt.

Task 2: Backend - Spatial Data Processing (scripts/process_data.py)
Buat script Python untuk mengotomatiskan ekstraksi KML dari dalam ZIP/KMZ, membersihkan data, dan mengekspornya ke format ringan.

Spesifikasi proses process_data.py:

Setup Driver: Aktifkan dukungan driver KML di fiona (fiona.drvsupport.supported_drivers['KML'] = 'rw').

Proses Coverage (89 KMZ):

Looping semua file .kmz di folder data/raw_coverage/.

Ekstrak .kml ke temporary folder.

Muat menggunakan geopandas.

Pembersihan: Drop kolom Description jika ada (ini memuat tabel HTML verbose yang bikin berat).

Gabungkan seluruh GeoDataFrame.

Kompresi: Gunakan metode .simplify(tolerance=0.0005, preserve_topology=True) pada kolom geometri.

Ekspor sebagai public/coverage.geojson.

Proses Tower BTS (1 KMZ):

Ekstrak file dari data/raw_tower/Tower_BTS_XL_Cilacap.kmz.

Muat menggunakan geopandas.

Pembersihan ekstrim: Hanya pertahankan kolom Name dan geometry.

Ekspor sebagai public/tower.geojson.

Task 3: Frontend - Web Viewer Development (public/index.html)
Buat UI peta berbasis HTML5/JS murni yang ringan dan responsif.

Spesifikasi public/index.html:

Library: Gunakan CDN untuk Leaflet.js (core map) dan plugin Leaflet.markercluster (wajib untuk menangani ribuan titik BTS agar render UI tidak macet).

Styling: width: 100vw; height: 100vh; margin: 0; agar fullscreen di layar HP.

Map Initialization: Atur center map di koordinat Cilacap [-7.7279, 109.0069] dengan zoom level 11.

Basemap: Gunakan tiles Google Streets http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}.

Layer Coverage: Fetch coverage.geojson, berikan style polygon sederhana (contoh: border biru statis, fill transparan), bind popup untuk menampilkan properties Name.

Layer Tower BTS: Fetch tower.geojson, masukkan titik-titik (gunakan L.circleMarker dengan radius kecil) ke dalam L.markerClusterGroup() sebelum menambahkannya ke peta. Bind popup untuk menampilkan properties Name.

Layer Control: Tambahkan widget control standar Leaflet di pojok kanan atas agar sales bisa mematikan/menyalakan layer Coverage dan layer Tower secara independen.

Task 4: Local Testing
Eksekusi ekstraksi data: python scripts/process_data.py.

Validasi direktori public/ telah berisi coverage.geojson dan tower.geojson.

Jalankan local server di dalam folder public/: python -m http.server 8000.

Buka browser IDE preview ke http://localhost:8000 untuk memastikan rendering marker cluster dan polygon berjalan smooth saat di-zoom.