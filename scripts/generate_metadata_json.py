"""
Generate JSON metadata files for each corpus image based on filename.
These are read by VisionService._load_from_json as a fallback when the API is unavailable.
"""
import json
import os

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")

TEMPLATES = {
    "fox": {
        "subject": "red fox",
        "category": "animal",
        "attributes": ["orange fur", "wild", "forest", "bushy tail"],
        "caption": "A red fox standing in a forest clearing with its distinctive orange coat.",
        "confidence": 0.95,
    },
    "wolf": {
        "subject": "gray wolf",
        "category": "animal",
        "attributes": ["gray fur", "wild", "pack animal", "forest"],
        "caption": "A gray wolf in its natural forest habitat, an apex predator of the wilderness.",
        "confidence": 0.95,
    },
    "dog": {
        "subject": "domestic dog",
        "category": "animal",
        "attributes": ["domestic", "friendly", "companion", "pet"],
        "caption": "A domestic dog, a loyal family companion known for its friendly nature.",
        "confidence": 0.95,
    },
    "bear": {
        "subject": "brown bear",
        "category": "animal",
        "attributes": ["brown fur", "large", "wild", "omnivore"],
        "caption": "A large brown bear in the wild, preparing for its seasonal hibernation.",
        "confidence": 0.95,
    },
    "deer": {
        "subject": "white-tailed deer",
        "category": "animal",
        "attributes": ["white tail", "graceful", "wild", "herbivore"],
        "caption": "A white-tailed deer in its natural habitat, alert and ready to flee.",
        "confidence": 0.95,
    },
}


def main():
    created = 0
    skipped = 0

    for filename in sorted(os.listdir(CORPUS_DIR)):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        prefix = "".join(c for c in filename.split(".")[0] if not c.isdigit())
        template = TEMPLATES.get(prefix)
        if template is None:
            print(f"No template for {filename}, skipping")
            continue

        json_path = os.path.join(CORPUS_DIR, os.path.splitext(filename)[0] + ".json")
        if os.path.exists(json_path):
            skipped += 1
            continue

        with open(json_path, "w") as f:
            json.dump(template, f, indent=2)
        print(f"Created {os.path.basename(json_path)}")
        created += 1

    print(f"\nDone: {created} created, {skipped} skipped")


if __name__ == "__main__":
    main()
