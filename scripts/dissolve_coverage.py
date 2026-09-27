import os
import json
import re
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.validation import make_valid

def dissolve_geojson(input_path, output_path):
    """Dissolve/union polygon per (district, net) in a coverage GeoJSON.
    - Groups features by (district, network type)
    - Unions geometries per group using unary_union (with make_valid for invalid inputs)
    - Overwrites the file with the dissolved FeatureCollection.
    - Keeps only essential properties: d (district), net (network), c (cluster), s (signal DBM).
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Group features by (district upper, network upper)
    groups = {}
    for feat in data.get('features', []):
        props = feat['properties']
        key = (props.get('d', '').upper(), props.get('net', '').upper())
        groups.setdefault(key, []).append(shape(feat['geometry']))

    merged_features = []
    for (district, net), geoms in groups.items():
        # Make each geometry valid before union
        valid_geoms = [make_valid(g) if not g.is_valid else g for g in geoms]
        try:
            u = unary_union(valid_geoms)
            if not u.is_valid:
                u = make_valid(u)
        except Exception as e:
            print(f"⚠️ Union error for {district}/{net}: {e}")
            # fallback: keep first geometry
            u = valid_geoms[0]

        # Build simplified properties for the merged feature
        # Ambil nilai utama dari features yang digabung
        nets = [f['properties'].get('net', '') for f in data['features'] if (f['properties'].get('d','').upper(), f['properties'].get('net','').upper()) == (district.upper(), net.upper())]
        dbms = [f['properties'].get('s', '') for f in data['features'] if (f['properties'].get('d','').upper(), f['properties'].get('net','').upper()) == (district.upper(), net.upper()) and f['properties'].get('s')]

        props = {
            'd': district or 'UNKNOWN',
            'net': ' + '.join(sorted(set(nets))) if nets else '',
            's': '; '.join([str(d) for d in dbms if d])[:50] if dbms else 'Tidak ada data',
            'c': data['features'][0]['properties'].get('c', ''),  # Ambil cluster dari feature pertama (satu dari banyak)
        }

        merged_feat = {
            'type': 'Feature',
            'geometry': mapping(u),
            'properties': props
        }
        merged_features.append(merged_feat)

    result = {
        'type': 'FeatureCollection',
        'district': district if groups else 'UNKNOWN',
        'features': merged_features
    }

    # Tulis output dengan separators minimal (compact)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    # Print size comparison
    orig_size_kb = os.path.getsize(input_path) / 1024
    new_size_kb = os.path.getsize(output_path) / 1024
    reduction = ((orig_size_kb - new_size_kb) / orig_size_kb) * 100
    print(f"🗺️ {os.path.basename(input_path)}:")
    print(f"   Sebelum: {orig_size_kb:.0f} KB → Setelah: {new_size_kb:.0f} KB ({reduction:.0f}% lebih kecil)")

def main():
    coverage_dir = 'public/coverage'
    if not os.path.isdir(coverage_dir):
        print(f"❌ Folder {coverage_dir} tidak ditemukan.")
        return

    # Dapatkan daftar file .geojson di folder coverage
    geojson_files = sorted([f for f in os.listdir(coverage_dir) if f.endswith('.geojson')])

    if not geojson_files:
        print("⚠️ Tidak ada file geojson di folder coverage.")
        return

    print(f"🔧 Menghilangkan overlap pada {len(geojson_files)} file coverage...\n")

    for fname in geojson_files:
        input_path = os.path.join(coverage_dir, fname)
        output_path = input_path  # overwrite di tempat yang sama
        dissolve_geojson(input_path, output_path)

    print(f"\n✅ Selesai! Semua {len(geojson_files)} file coverage telah di-optimalkan.")


if __name__ == '__main__':
    main()