"""
Generate placeholder corpus images locally using PIL.
No internet required. Creates 50 real JPG files in corpus/.

Usage:
    python scripts/generate_corpus.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")

CATEGORIES = {
    "fox":  {"color": (210, 105, 30),  "label": "Red Fox",       "count": 10},
    "wolf": {"color": (105, 105, 105), "label": "Gray Wolf",      "count": 10},
    "dog":  {"color": (210, 180, 140), "label": "Dog",            "count": 10},
    "bear": {"color": (139, 90, 43),   "label": "Brown Bear",     "count": 10},
    "deer": {"color": (144, 188, 102), "label": "White-tail Deer","count": 10},
}

WIDTH, HEIGHT = 400, 300


def make_image(label: str, index: int, bg_color: tuple, dest: str) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=bg_color)
    draw = ImageDraw.Draw(img)

    # dark overlay box for text
    draw.rectangle([20, HEIGHT // 2 - 40, WIDTH - 20, HEIGHT // 2 + 40], fill=(0, 0, 0, 180))

    text = f"{label} #{index}"
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((WIDTH - tw) / 2, HEIGHT / 2 - th / 2), text, fill=(255, 255, 255), font=font)

    img.save(dest, "JPEG", quality=85)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    created = 0
    skipped = 0

    for prefix, info in CATEGORIES.items():
        for i in range(1, info["count"] + 1):
            filename = f"{prefix}{i}.jpg"
            dest = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(dest):
                print(f"Skipping {filename} (exists)")
                skipped += 1
                continue
            make_image(info["label"], i, info["color"], dest)
            print(f"Created {filename}")
            created += 1

    print(f"\nDone: {created} created, {skipped} skipped")
    print(f"Corpus: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
