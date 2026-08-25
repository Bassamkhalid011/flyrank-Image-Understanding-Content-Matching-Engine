"""
Generate pre-defined metadata JSON files for each corpus image.
These simulate Gemini Vision output (same schema, same Pydantic validation).
The VisionService reads these files when no API key is available.

Usage:
    python scripts/generate_metadata_json.py
"""
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")

TEMPLATES = {
    "fox": {
        "subject": "red fox",
        "category": "animal",
        "attributes": ["orange fur", "bushy tail", "pointed ears", "wild", "forest"],
        "caption": "A red fox (Vulpes vulpes) with distinctive orange fur standing in a natural habitat.",
        "confidence": 0.93,
    },
    "wolf": {
        "subject": "gray wolf",
        "category": "animal",
        "attributes": ["gray coat", "pack animal", "apex predator", "wild", "forest"],
        "caption": "A gray wolf (Canis lupus) in its natural forest environment.",
        "confidence": 0.91,
    },
    "dog": {
        "subject": "domestic dog",
        "category": "animal",
        "attributes": ["friendly", "domesticated", "companion animal", "fur coat"],
        "caption": "A domestic dog, a loyal companion animal bred to live alongside humans.",
        "confidence": 0.95,
    },
    "bear": {
        "subject": "brown bear",
        "category": "animal",
        "attributes": ["brown fur", "large", "omnivore", "wild", "powerful"],
        "caption": "A brown bear (Ursus arctos) in the wild, a powerful omnivore.",
        "confidence": 0.92,
    },
    "deer": {
        "subject": "white-tailed deer",
        "category": "animal",
        "attributes": ["slender", "antlers", "white tail", "graceful", "woodland"],
        "caption": "A white-tailed deer (Odocoileus virginianus) in a woodland meadow.",
        "confidence": 0.90,
    },
}

COUNTS = {"fox": 10, "wolf": 10, "dog": 10, "bear": 10, "deer": 10}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    created = 0

    for prefix, count in COUNTS.items():
        template = TEMPLATES[prefix]
        for i in range(1, count + 1):
            filename = f"{prefix}{i}.json"
            dest = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(dest):
                print(f"Skipping {filename} (exists)")
                continue
            with open(dest, "w") as f:
                json.dump(template, f, indent=2)
            print(f"Created {filename}")
            created += 1

    print(f"\nDone: {created} JSON metadata files created in {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    main()
