"""Download the SUPPORT2 dataset (UCI ML Repository, id 880) into data/raw/.

    python scripts/download_data.py

Result:
    data/raw/support2.csv   (9,105 patients x 48 columns)

The file is checked against a SHA-256 checksum, so every group member works on
the same data. Safe to re-run: an existing, valid file is kept.
"""
import hashlib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
URL = "https://archive.ics.uci.edu/static/public/880/data.csv"
DEST = RAW / "support2.csv"
SHA256 = "9da794bbd5c3a6a816e677cc17535e58c122d9ef4cbefd404489330a9f9cd2de"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    if DEST.exists() and sha256(DEST) == SHA256:
        print(f"{DEST.name}: already downloaded")
        return
    print(f"Downloading {URL}")
    with urllib.request.urlopen(URL, timeout=60) as r:
        data = r.read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("checksum mismatch: the file on UCI differs from the one this project was built on")
    DEST.write_bytes(data)
    print(f"{DEST.name}: done ({len(data):,} bytes)")


if __name__ == "__main__":
    main()
