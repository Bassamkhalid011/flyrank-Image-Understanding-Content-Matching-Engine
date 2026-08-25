"""
Copy and rename images from the Kaggle animal dataset into corpus/.

Usage:
    python scripts/copy_from_kaggle.py
"""
import os
import shutil

KAGGLE_DIR = r"C:\Users\Bassam Khalid\Downloads\animals\animals"
CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")

# Map: corpus prefix -> kaggle folder name, count to copy
MAPPING = {
    "fox":  ("fox",  10),
    "wolf": ("wolf", 10),
    "dog":  ("dog",  10),
    "bear": ("bear", 10),
    "deer": ("deer", 10),
}


def main():
    os.makedirs(CORPUS_DIR, exist_ok=True)
    copied = 0
    skipped = 0

    for prefix, (folder, count) in MAPPING.items():
        src_dir = os.path.join(KAGGLE_DIR, folder)
        if not os.path.exists(src_dir):
            print(f"WARNING: folder not found — {src_dir}")
            continue

        files = sorted([
            f for f in os.listdir(src_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ])[:count]

        for i, filename in enumerate(files, start=1):
            dest_name = f"{prefix}{i}.jpg"
            dest = os.path.join(CORPUS_DIR, dest_name)

            if os.path.exists(dest):
                print(f"Skipping {dest_name} (exists)")
                skipped += 1
                continue

            src = os.path.join(src_dir, filename)
            shutil.copy2(src, dest)
            print(f"Copied {folder}/{filename} -> corpus/{dest_name}")
            copied += 1

    # Remove any old JSON metadata files so live Gemini API is used
    json_removed = 0
    for f in os.listdir(CORPUS_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(CORPUS_DIR, f))
            json_removed += 1

    total = sum(1 for f in os.listdir(CORPUS_DIR) if f.endswith(".jpg"))
    print(f"\nDone: {copied} copied, {skipped} skipped")
    print(f"Removed {json_removed} old JSON metadata files (live API will be used)")
    print(f"Total images in corpus/: {total}")


if __name__ == "__main__":
    main()
