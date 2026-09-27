import os
import glob
import json
import zipfile
import re
import xml.etree.ElementTree as ET
from datetime import datetime

NS = {'kml': 'http://www.opengis.net/kml/2.2'}

def parse_html_table(html_str):
    if not html_str:
        return {}
    props = {}
    rows = re.findall(r'<tr>(.*?)</tr>', html_str, re.DOTALL | re.IGNORECASE)
    for row in rows:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
        if len(tds) >= 2:
            key = re.sub(r'<.*?>', '', tds[0]).strip()
            val = re.sub(r'<.*?>', '', tds[1]).strip()
            if key:
                props[key] = val
    return props

def parse_coordinates(coord_text, precision=5):
    coords = []
    for point_str in coord_text.strip().split():
        parts = point_str.split(',')
        if len(parts) >= 2:
            try:
                lng = round(float(parts[0]), precision)
                lat = round(float(parts[1]), precision)
                coords.append([lng, lat])
            except ValueError:
                continue
    return coords

def process_towers():
    print("\n--- Processing Tower BTS KMZ ---")
    tower_kmz_path = 'data/raw_tower/Tower_BTS_XL_Cilacap.kmz'
    if not os.path.exists(tower_kmz_path):
        files = glob.glob('data/raw_tower/*.kmz')
        if files:
            tower_kmz_path = files[0]
        else:
            print("Tower KMZ file not found in data/raw_tower/")
            return []

    features = []
    with zipfile.ZipFile(tower_kmz_path, 'r') as z:
        kml_names = [n for n in z.namelist() if n.endswith('.kml')]
        if not kml_names:
            print("No KML in Tower KMZ")
            return []
        with z.open(kml_names[0]) as f:
            root = ET.fromstring(f.read())
            placemarks = root.findall('.//kml:Placemark', NS)
            if not placemarks:
                placemarks = root.findall('.//Placemark')

            for p in placemarks:
                name_el = p.find('kml:name', NS)
                if name_el is None:
                    name_el = p.find('name')
                name = name_el.text.strip() if name_el is not None and name_el.text else "Tower BTS XL"

                desc_el = p.find('kml:description', NS)
                if desc_el is None:
                    desc_el = p.find('description')
                desc_text = desc_el.text if desc_el is not None and desc_el.text else ""

                details = {}
                for line in desc_text.replace('&nbsp;', ' ').split('<br>'):
                    clean_line = re.sub(r'<.*?>', '', line).strip()
                    if ':' in clean_line:
                        k, v = clean_line.split(':', 1)
                        details[k.strip().lower().replace(' ', '_')] = v.strip()

                style_el = p.find('kml:styleUrl', NS)
                if style_el is None:
                    style_el = p.find('styleUrl')
                style_url = style_el.text.strip() if style_el is not None and style_el.text else ""
                color_match = re.search(r'([A-Fa-f0-9]{6})', style_url)
                color_hex = f"#{color_match.group(1)}" if color_match else "#ff007a"

                point_el = p.find('.//kml:Point//kml:coordinates', NS)
                if point_el is None:
                    point_el = p.find('.//Point//coordinates')

                if point_el is not None and point_el.text:
                    parts = point_el.text.strip().split(',')
                    if len(parts) >= 2:
                        lng = round(float(parts[0]), 6)
                        lat = round(float(parts[1]), 6)
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "name": name,
                                "tower_id": details.get("towerid", ""),
                                "enbid": details.get("enbid", ""),
                                "district": details.get("district", ""),
                                "ran_type": details.get("ran_type", ""),
                                "city_5g": details.get("city_5g", ""),
                                "antenna_height": details.get("antenna_height", ""),
                                "spv": details.get("spv", ""),
                                "payload": details.get("remark_payload", ""),
                                "color": color_hex,
                                "style_url": style_url
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lng, lat]
                            }
                        })

    geojson = {
        "type": "FeatureCollection",
        "total_features": len(features),
        "features": features
    }

    os.makedirs('public', exist_ok=True)
    out_path = 'public/tower.geojson'
    with open(out_path, 'w', encoding='utf-8') as out_f:
        json.dump(geojson, out_f, separators=(',', ':'))

    file_size_kb = os.path.getsize(out_path) / 1024
    print(f"Done Towers: {len(features)} towers written to {out_path} ({file_size_kb:.1f} KB)")
    return features

def process_kmz_files():
    print("\n--- Processing Coverage & Building KMZ files ---")
    kmz_files = glob.glob('data/raw_coverage/**/*.kmz', recursive=True)
    print(f"Found {len(kmz_files)} KMZ coverage/building files.")

    coverage_by_district = {}
    buildings_by_district = {}
    district_stats = {}

    total_polys = 0
    total_buildings = 0

    for idx, kmz_path in enumerate(kmz_files, 1):
        # Fallback district/village from path if not in properties
        parts = os.path.normpath(kmz_path).split(os.sep)
        path_district = ""
        path_village = ""
        if len(parts) >= 4:
            path_district = parts[-3].upper()
            path_village = parts[-2].upper()

        try:
            with zipfile.ZipFile(kmz_path, 'r') as z:
                kml_names = [n for n in z.namelist() if n.endswith('.kml')]
                if not kml_names:
                    continue
                with z.open(kml_names[0]) as f:
                    root = ET.fromstring(f.read())
                    placemarks = root.findall('.//kml:Placemark', NS)
                    if not placemarks:
                        placemarks = root.findall('.//Placemark')

                    for p in placemarks:
                        name_el = p.find('kml:name', NS)
                        if name_el is None:
                            name_el = p.find('name')
                        name = name_el.text.strip() if name_el is not None and name_el.text else ""

                        desc_el = p.find('kml:description', NS)
                        if desc_el is None:
                            desc_el = p.find('description')
                        desc_text = desc_el.text if desc_el is not None and desc_el.text else ""
                        table_data = parse_html_table(desc_text)

                        district = table_data.get("DISTRICT", table_data.get("KECAMATAN", path_district)).strip().upper()
                        village = table_data.get("VILLAGE", table_data.get("DESA", path_village)).strip().upper()
                        cluster = table_data.get("DSA_CLUSTER_ID", name).strip()
                        network = table_data.get("NETWORK_TYPE", table_data.get("NETWORK_AVAILABLE", "FWA")).strip()

                        if not district:
                            district = path_district or "LAINNYA"

                        # Check if Point (Building) or Polygon (Coverage)
                        point_el = p.find('.//kml:Point//kml:coordinates', NS)
                        if point_el is None:
                            point_el = p.find('.//Point//coordinates')

                        if point_el is not None and point_el.text:
                            # BUILDING PLACEMARK
                            coords = parse_coordinates(point_el.text, precision=6)
                            if coords:
                                lng, lat = coords[0]
                                b_id = table_data.get("BUILDING_ID", name)
                                priority = table_data.get("FLAG_PRIORITY", "")
                                category = table_data.get("CATEGORY", "")
                                homepass = table_data.get("HOMEPASSID", "")

                                b_feat = {
                                    "type": "Feature",
                                    "properties": {
                                        "id": b_id,
                                        "c": cluster,
                                        "d": district,
                                        "v": village,
                                        "net": network,
                                        "prio": priority,
                                        "cat": category,
                                        "hp": "" if homepass == "NULL" else homepass
                                    },
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": [lng, lat]
                                    }
                                }
                                if district not in buildings_by_district:
                                    buildings_by_district[district] = []
                                buildings_by_district[district].append(b_feat)
                                total_buildings += 1

                        else:
                            # POLYGON COVERAGE PLACEMARK
                            poly_els = p.findall('.//kml:Polygon', NS)
                            if not poly_els:
                                poly_els = p.findall('.//Polygon')

                            if poly_els:
                                rings = []
                                for poly in poly_els:
                                    outer = poly.find('.//kml:outerBoundaryIs//kml:coordinates', NS)
                                    if outer is None:
                                        outer = poly.find('.//outerBoundaryIs//coordinates')
                                    if outer is not None and outer.text:
                                        ring = parse_coordinates(outer.text, precision=5)
                                        if len(ring) >= 4:
                                            rings.append(ring)

                                if rings:
                                    dbm = table_data.get("DBM", "").strip()
                                    c_feat = {
                                        "type": "Feature",
                                        "properties": {
                                            "c": cluster,
                                            "d": district,
                                            "v": village,
                                            "net": network,
                                            "s": dbm
                                        },
                                        "geometry": {
                                            "type": "Polygon" if len(rings) == 1 else "MultiPolygon",
                                            "coordinates": rings if len(rings) == 1 else [[r] for r in rings]
                                        }
                                    }
                                    if district not in coverage_by_district:
                                        coverage_by_district[district] = []
                                    coverage_by_district[district].append(c_feat)
                                    total_polys += 1

                        if district not in district_stats:
                            district_stats[district] = {"coverage": 0, "buildings": 0}

        except Exception as e:
            print(f"Error processing {kmz_path}: {e}")

        if idx % 15 == 0 or idx == len(kmz_files):
            print(f"Processed [{idx}/{len(kmz_files)}] KMZ files... Polygons: {total_polys}, Buildings: {total_buildings}")

    # Output directories
    os.makedirs('public/coverage', exist_ok=True)
    os.makedirs('public/buildings', exist_ok=True)

    # Export Coverage per district
    for dist, feats in coverage_by_district.items():
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', dist)
        if dist in district_stats:
            district_stats[dist]["coverage"] = len(feats)
        with open(f'public/coverage/{safe_name}.geojson', 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "district": dist, "features": feats}, f, separators=(',', ':'))

    # Export Buildings per district
    for dist, feats in buildings_by_district.items():
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', dist)
        if dist in district_stats:
            district_stats[dist]["buildings"] = len(feats)
        with open(f'public/buildings/{safe_name}.geojson', 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "district": dist, "features": feats}, f, separators=(',', ':'))

    # Export districts summary index
    with open('public/districts.json', 'w', encoding='utf-8') as f:
        json.dump(district_stats, f, indent=2)

    print(f"\nSUCCESS:")
    print(f"  - Total Coverage Polygons: {total_polys} across {len(coverage_by_district)} districts")
    print(f"  - Total Building Prospects: {total_buildings} across {len(buildings_by_district)} districts")
    print(f"  - All district files exported to public/coverage/ and public/buildings/")

if __name__ == '__main__':
    start = datetime.now()
    process_towers()
    process_kmz_files()
    duration = datetime.now() - start
    print(f"\nAll data extracted & indexed in {duration.total_seconds():.2f}s!")
