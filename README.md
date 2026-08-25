# AI Image Understanding & Content Matching Engine

FlyRank Backend Capstone (BE track). A service that understands what's in an
image, matches images to blog posts by semantic content, and refuses to
suggest a match it isn't confident about.

## What it does

1. **Understand** — every image in a corpus is sent to Gemini 2.5 Flash (vision),
   which returns structured tags (subject, category, attributes, caption, confidence)
   validated against a strict Pydantic schema.
2. **Embed** — captions and post content are embedded into 3072-dim vectors using
   `gemini-embedding-001` so matching is semantic (a post about "Vulpes vulpes"
   can still match an image tagged "red fox").
3. **Match** — for a given post, candidate images are ranked by cosine similarity
   between the post embedding and each image caption embedding.
4. **Guard** — before a match is suggested, a mismatch guard checks similarity
   threshold, image confidence flag, and category alignment. It rejects with a
   human-readable reason, or reports "no confident match" rather than guessing.
5. **Review** — matches are surfaced through an API for a human to approve or
   reject, with a full explanation available for every decision.

## Architecture

```
                 ┌──────────────────┐
   corpus/*.jpg  │                  │
  ──────────────▶│  Vision Model    │  gemini-2.5-flash, JSON-schema output
                 │  (VisionService) │  → falls back to corpus/*.json if no quota
                 └────────┬─────────┘
                          │ tags + confidence
                          ▼
                 ┌──────────────────┐
                 │ Tags/Caption     │
                 │ + Embedding      │  gemini-embedding-001 (3072-dim)
                 └────────┬─────────┘
                          │ stored in Postgres (Image table)
                          ▼
   Post text ──▶ ┌──────────────────┐
   + embedding   │  Matching Engine │  cosine similarity, top-10 candidates
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │  Mismatch Guard  │  threshold / flagged / category checks
                 │                  │  → ACCEPT (with reason) or REJECT (with reason)
                 └────────┬─────────┘
                          ▼
                 ┌──────────────────┐
                 │   Review API     │  approve / reject / explain
                 └──────────────────┘
```

## SDK & Models Used

| Component | Model | SDK |
|-----------|-------|-----|
| Vision (image tagging) | `gemini-2.5-flash` | `google-genai` |
| Embeddings | `gemini-embedding-001` | `google-genai` |

> **Note on free-tier API keys:** Google AI Studio now issues OAuth-style keys
> (`AQ.Ab8R...`) instead of the classic `AIza...` keys. Both work with the
> `google-genai` SDK. The older `google-generativeai` package does not support
> these keys — which is why this project was upgraded to `google-genai`.

## Run steps

```bash
# 1. Configure
copy .env.example .env        # fill in GEMINI_API_KEY

# 2. Start Postgres + app
docker compose up -d

# 3. Seed images and posts
python scripts/generate_corpus.py     # generates 50 placeholder images locally
python scripts/generate_metadata_json.py  # generates JSON metadata for each image
python scripts/seed_posts.py          # inserts 10 blog posts with real embeddings

# 4. Process images (reads JSON metadata + generates embeddings via API)
curl -X POST http://localhost:8000/images/process \
  -H "Content-Type: application/json" \
  -d "{\"image_dir\": \"./corpus\"}"

# 5. Run tests
pytest tests/ -v

# 6. Run eval
python eval/run_eval.py
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/images/process` | Trigger batch vision job on image directory |
| GET | `/posts/{post_id}/images` | Ranked image suggestions for a post |
| POST | `/suggestions/{id}/approve` | Approve a suggestion |
| POST | `/suggestions/{id}/reject` | Reject a suggestion (with reason) |
| GET | `/suggestions/{id}/explain` | Full explanation of a suggestion decision |
| GET | `/jobs/costs` | Cost log for all vision/embedding calls |
| GET | `/health` | Health check |

## Eval precision

Top-1 Precision: **see eval/results.json after running `python eval/run_eval.py`**

(Target: ≥ 70% on the 20-pair hand-labeled set.)

## Limitations

- Evaluated on a small hand-labeled set (~20 pairs); thresholds are tuned on
  that data and may not generalise beyond the five animal categories.
- Google AI Studio now issues OAuth-style API keys (`AQ.Ab8R...`) instead of
  the classic `AIza...` format. These only work with the new `google-genai` SDK —
  the older `google-generativeai` package does not support them.
- Category-mismatch detection is a keyword heuristic — it can miss synonyms
  not in its keyword list.
- The `Vector` column stores embeddings as JSON text (SQLite-compatible for
  tests; Postgres in production). Native pgvector would be faster at scale.
