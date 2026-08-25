# AI Image Understanding & Content Matching Engine

FlyRank Backend Capstone (BE track). A service that understands what's in an
image, matches images to blog posts by semantic content, and refuses to
suggest a match it isn't confident about.

## What it does

1. **Understand** — every image in a corpus is sent to a vision model
   (Gemini Flash), which returns structured tags (subject, category,
   attributes, caption, confidence) validated against a strict Pydantic schema.
2. **Embed** — captions and post content are embedded into vectors so
   matching is semantic (a post about "Vulpes vulpes" can still match an
   image tagged "red fox").
3. **Match** — for a given post, candidate images are ranked by cosine
   similarity between the post embedding and each image's caption embedding.
4. **Guard** — before a match is suggested, a mismatch guard checks
   similarity threshold, image confidence flag, and category alignment. It
   rejects with a human-readable reason, or reports "no confident match"
   rather than guessing.
5. **Review** — matches are surfaced through an API for a human to approve
   or reject, with a full explanation available for every decision.

## Architecture

```
                 ┌──────────────┐
   corpus/*.jpg  │              │
  ──────────────▶│ Vision Model │  (Gemini Flash, JSON-schema output)
                 │ (VisionSvc)  │
                 └──────┬───────┘
                        │ tags + confidence
                        ▼
                 ┌──────────────┐
                 │  Tags/Caption │
                 │  + Embedding  │  (EmbeddingService → text-embedding-004)
                 └──────┬───────┘
                        │ stored in Postgres (Image table)
                        ▼
   Post text ──▶ ┌──────────────┐
   + embedding   │   Matching   │  cosine similarity, top-10 candidates
                 │    Engine    │
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  Mismatch    │  threshold / flagged / category checks
                 │   Guard      │  → ACCEPT (with reason) or REJECT (with reason)
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  Review API  │  approve / reject / explain
                 └──────────────┘
```

## Run steps

```bash
# 1. Configure
cp .env.example .env          # fill in GEMINI_API_KEY

# 2. Start Postgres + app
docker compose up -d

# 3. Seed data
python scripts/seed_corpus.py # downloads ~50 images into corpus/
python scripts/seed_posts.py  # inserts 10 blog posts with embeddings

# 4. Process images (starts background job via API)
curl -X POST http://localhost:8000/images/process \
  -H "Content-Type: application/json" \
  -d '{"image_dir": "./corpus"}'

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

(Target: ≥ 70% on the 20-pair hand-labeled set; actual number filled in
after running against a live DB with processed images.)

## Limitations

- Evaluated on a small hand-labeled set (~20 pairs); thresholds are tuned
  on that data and may not generalise far beyond the five animal categories
  in the sample corpus.
- Vision calls depend on a free-tier Gemini quota, which can rate-limit or
  reject new API keys. See `BUILDLOG.md` for how this was handled.
- Category-mismatch detection is a keyword heuristic, not a learned
  classifier — it can miss synonyms it wasn't given a keyword for.
- The `Vector` column stores embeddings as JSON text (compatible with both
  SQLite for tests and Postgres in production); a native pgvector ARRAY
  column would give better index performance at scale.
