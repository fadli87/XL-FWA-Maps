import subprocess
import glob
import os
import sys

def run(cmd):
    print(f">> {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr and res.returncode != 0:
        print(f"Error: {res.stderr.strip()}", file=sys.stderr)
    return res.returncode == 0

def push_in_batches():
    print("=== Step 1: Base App Files ===")
    run('git add README.md .gitignore requirements.txt scripts/ public/index.html public/districts.json public/tower.geojson')
    run('git commit -m "Add core web app and metadata"')
    run('git push -u origin master:main')

    print("\n=== Step 2: Building GeoJSON files ===")
    bldg_files = glob.glob('public/buildings/*.geojson')
    # Push in batches of 6 files (~35MB per batch)
    for i in range(0, len(bldg_files), 6):
        batch = bldg_files[i:i+6]
        files_str = " ".join([f'"{f}"' for f in batch])
        print(f"Adding building batch {i//6 + 1}: {len(batch)} files")
        run(f'git add {files_str}')
        run(f'git commit -m "Add building dataset batch {i//6 + 1}"')
        run('git push origin master:main')

    print("\n=== Step 3: Coverage GeoJSON files ===")
    cov_files = glob.glob('public/coverage/*.geojson')
    # Push in batches of 4 files (~60MB per batch)
    for i in range(0, len(cov_files), 4):
        batch = cov_files[i:i+4]
        files_str = " ".join([f'"{f}"' for f in batch])
        print(f"Adding coverage batch {i//4 + 1}: {len(batch)} files")
        run(f'git add {files_str}')
        run(f'git commit -m "Add coverage dataset batch {i//4 + 1}"')
        run('git push origin master:main')

    print("\n=== Step 4: Raw KMZ files ===")
    kmz_files = glob.glob('data/**/*.kmz', recursive=True)
    for i in range(0, len(kmz_files), 15):
        batch = kmz_files[i:i+15]
        files_str = " ".join([f'"{f}"' for f in batch])
        print(f"Adding raw KMZ batch {i//15 + 1}: {len(batch)} files")
        run(f'git add {files_str}')
        run(f'git commit -m "Add raw KMZ data batch {i//15 + 1}"')
        run('git push origin master:main')

    print("\nAll files successfully pushed to GitHub!")

if __name__ == '__main__':
    push_in_batches()
