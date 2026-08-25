"""
Download sample animal images from Unsplash Source (no API key required).

Usage:
    python scripts/seed_corpus.py

Downloads ~50 images into ./corpus/ (10 each: fox, wolf, dog, bear, deer).
Existing files are skipped (idempotent).
"""
import os
import sys
import time

import requests

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")

CATEGORIES = {
    "fox":  ("red fox", 10),
    "wolf": ("gray wolf", 10),
    "dog":  ("dog", 10),
    "bear": ("brown bear", 10),
    "deer": ("white tailed deer", 10),
}

# Unsplash Source API — free, no key required, 400x300 images
UNSPLASH_URL = "https://source.unsplash.com/400x300/?{query}&sig={sig}"


def download_image(url: str, dest: str) -> bool:
    try:
        resp = requests.get(url, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(dest, "wb") as f:
                f.write(resp.content)
            return True
        print(f"  Warning: unexpected response {resp.status_code} for {url}")
        return False
    except Exception as exc:
        print(f"  Error downloading {url}: {exc}")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    downloaded = 0
    skipped = 0

    for prefix, (query, count) in CATEGORIES.items():
        query_encoded = query.replace(" ", "%20")
        for i in range(1, count + 1):
            filename = f"{prefix}{i}.jpg"
            dest = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(dest) and os.path.getsize(dest) > 1000:
                print(f"Skipping {filename} (already exists)")
                skipped += 1
                continue

            url = UNSPLASH_URL.format(query=query_encoded, sig=f"{prefix}{i}")
            print(f"Downloading {filename} from Unsplash ({query})...")
            ok = download_image(url, dest)
            if ok:
                downloaded += 1
            time.sleep(0.3)  # be polite to Unsplash

    print(f"\nDone: downloaded {downloaded} images, skipped {skipped}")
    print(f"Images in: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
