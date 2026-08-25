"""
Precision evaluation script.

Usage:
    python eval/run_eval.py

Requires the app's DATABASE_URL to be set (either via .env or env var).
The DB must already contain processed images and embedded posts.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.matching import MatchingEngine
from app.db.session import SessionLocal

EVAL_SET = os.path.join(os.path.dirname(__file__), "eval_set.json")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")


def main():
    with open(EVAL_SET) as f:
        pairs = json.load(f)

    db = SessionLocal()
    engine = MatchingEngine(db=db)

    correct = 0
    total = len(pairs)
    results = []

    for pair in pairs:
        post_id = pair["post_id"]
        expected_filename = pair["correct_image_filename"]

        outcome = engine.rank_and_guard(post_id)
        suggested = outcome.get("suggested")
        top_filename = suggested["image"].filename if suggested else None
        hit = top_filename == expected_filename

        if hit:
            correct += 1

        results.append({
            "post_id": post_id,
            "expected": expected_filename,
            "got": top_filename,
            "hit": hit,
            "no_match": outcome["no_match"],
            "explanation": outcome["explanation"],
        })
        print(
            f"post {post_id}: expected={expected_filename!r} got={top_filename!r} "
            f"{'HIT' if hit else 'MISS'}"
        )

    precision = correct / total if total else 0.0
    print(f"\nTop-1 Precision: {correct}/{total} = {precision:.0%}")

    with open(RESULTS_FILE, "w") as f:
        json.dump({"precision": precision, "correct": correct, "total": total, "rows": results}, f, indent=2)

    print(f"Results saved to {RESULTS_FILE}")
    db.close()


if __name__ == "__main__":
    main()
