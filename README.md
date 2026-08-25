# AI Image Understanding & Content Matching Engine

FlyRank Backend Capstone (BE track). A service that understands what's in an
image, matches images to blog posts by semantic content, and refuses to
suggest a match it isn't confident about.

## What it does

1. **Understand** — every image in a corpus is sent to a vision model
   (Gemini Flash), which returns structured tags (subject, category,
   attributes, caption, confidence) validated against a strict schema.
2. **Embed** — captions and post content are embedded into vectors so
   matching is semantic (a post about "Vulpes vulpes" can still match an
   image tagged "red fox").
3. **Match** — for a given post, candidate images are ranked by cosine
   similarity between the post embedding and each image's caption
   embedding.
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
                 │  + Embedding  │  (EmbeddingService)
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
cp .env.example .env          # fill in GEMINI_API_KEY
docker compose up -d          # Postgres (pgvector) + app
python scripts/seed_corpus.py # downloads sample images into corpus/
python scripts/seed_posts.py  # inserts sample blog posts
curl -X POST localhost:8000/images/process -d '{"image_dir": "./corpus"}' -H "Content-Type: application/json"
pytest tests/ -v
python eval/run_eval.py
```

## Limitations

- Evaluated on a small hand-labeled set (~15-20 pairs); thresholds are
  tuned on that data and may not generalize far beyond the five animal
  categories in the sample corpus.
- Vision calls depend on a free-tier Gemini quota, which can rate-limit
  or reject new API keys. See `BUILDLOG.md` for how this was handled.
- Category-mismatch detection is a keyword heuristic, not a learned
  classifier — it can miss synonyms it wasn't given a keyword for.

This README is filled in further (final precision number, etc.) at the
end of the build — see later commits.
