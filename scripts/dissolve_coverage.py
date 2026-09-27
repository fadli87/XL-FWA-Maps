"""
Dissolve (union) coverage polygons per network type within each district.
Raw coverage files have one polygon per building-level coverage cell (often
overlapping/adjacent). Merging same-category polygons into a handful of
blob shapes per district cuts file size by orders of magnitude while
preserving exact boundary information for the "am I covered?" use case.

Trade-off: per-polygon fields that vary cell-to-cell (signal DBM, cluster,
village) are dropped since they no longer apply to a merged shape. Only
network type (net) and district (d) are kept. Raw per-cell data still lives
in data/raw_coverage/ if finer detail is ever needed again.
"""
import glob
import json
import os

from shapely.geometry import shape, mapping
from shapely.ops import unary_union

COORD_PRECISION = 5  # ~1.1m, matches original extraction precision


def round_coords(geom_mapping, ndigits):
    def rnd(coords):
        if isinstance(coords[0], (list, tuple)):
            return [rnd(c) for c in coords]
        return [round(coords[0], ndigits), round(coords[1], ndigits)]
    geom_mapping['coordinates'] = rnd(geom_mapping['coordinates'])
    return geom_mapping


def dissolve_file(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    district = data.get('district', os.path.splitext(os.path.basename(path))[0])
    by_net = {}
    for feat in data['features']:
        net = feat['properties'].get('net', 'FWA')
        geom = shape(feat['geometry'])
        if not geom.is_valid:
            geom = geom.buffer(0)  # cheap fix for self-intersecting rings
        by_net.setdefault(net, []).append(geom)

    out_features = []
    for net, geoms in by_net.items():
        merged = unary_union(geoms)
        if merged.is_empty:
            continue
        geom_map = round_coords(mapping(merged), COORD_PRECISION)
        out_features.append({
            "type": "Feature",
            "properties": {"d": district, "net": net},
            "geometry": geom_map
        })

    before_count = len(data['features'])
    before_size = os.path.getsize(path)

    out = {"type": "FeatureCollection", "district": district, "features": out_features}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, separators=(',', ':'))

    after_size = os.path.getsize(path)
    print(f"{district:20s} {before_count:>7d} polys -> {len(out_features):>2d} blobs | "
          f"{before_size/1e6:6.2f} MB -> {after_size/1e6:6.2f} MB")


def main():
    files = sorted(glob.glob('public/coverage/*.geojson'))
    print(f"Dissolving {len(files)} district coverage files...\n")
    total_before = sum(os.path.getsize(f) for f in files)
    for path in files:
        dissolve_file(path)
    total_after = sum(os.path.getsize(f) for f in files)
    print(f"\nTOTAL: {total_before/1e6:.1f} MB -> {total_after/1e6:.1f} MB "
          f"({total_before/max(total_after,1):.1f}x smaller)")


if __name__ == '__main__':
    main()
