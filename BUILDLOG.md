# Build Log

Honest record of what AI (Claude) generated, where it was wrong, and what was changed.

---

## Phase 1 — Design & Scaffold

**Claude helped:** Generated the initial project structure, README architecture diagram,
Docker setup, `pydantic-settings` config, and SQLAlchemy models in one pass.

**What was wrong / changed:**
- The original `Image.embedding` column used SQLAlchemy `ARRAY(Float)` — this is
  Postgres-only and breaks SQLite test runs. Fixed by writing a custom `Vector`
  TypeDecorator that serialises to JSON text, making it work with both backends.

---

## Phase 2 — Image Understanding Pipeline

**Claude helped:** `VisionService` used `response_mime_type="application/json"` which
is the correct way to force Gemini to return JSON. This was not obvious from the docs.

**What was wrong / changed:**
- The prompt template had an off-by-one in the retry counter; the final attempt still
  caught exceptions instead of raising — corrected so `VisionError` is always raised
  after `MAX_RETRIES`.
- `BatchVisionJob` originally had a double-counting bug for `failed` images;
  the retry logic was refactored into `_process_one` to separate concerns clearly.

---

## Phase 3 — Matching Engine & Mismatch Guard

**Claude helped:** Suggested the cosine similarity with numpy and the top-K candidate
pattern. The `MismatchGuard` checking three independent rules in order was a clean
design that mapped well to the spec.

**What was wrong / changed:**
- The `category_mismatch` heuristic needed manual keyword tuning. The AI's first
  pass missed "Vulpes vulpes" as a fox synonym in the keyword list — added it.
- Guard was originally checking the first failing rule and stopping (short-circuit).
  Spec says check ALL — kept it that way since each rule is independent.

---

## Phase 4 — API Routes

**Claude helped:** FastAPI route scaffolding and `BackgroundTasks` usage for the batch
job. The `dependency_overrides` pattern for SQLite in tests was also suggested here.

**What was wrong / changed:**
- First version of `GET /posts/{post_id}/images` didn't save `ImageSuggestion` rows.
  Fixed so every candidate (accepted or rejected) is persisted for the review workflow.

---

## Phase 5 — Eval & Scripts

**Claude helped:** `run_eval.py` structure and the Unsplash Source URL pattern for
free image downloads.

**What was wrong / changed:**
- Unsplash Source API has been deprecated and may redirect or return 404 for some
  queries. If `seed_corpus.py` fails, manually download images and place them in
  `corpus/` with the naming convention `{category}{n}.jpg`.

---

## Vision API workaround (as described in FlyRank support ticket)

At the time of submission, all free-tier Gemini accounts had 0 quota on new API keys,
Groq had decommissioned all free vision models, and OpenRouter required paid credits.

**Approach taken (approved by FlyRank support):**
- `VisionService.classify_image()` works with a real Gemini API key when one is
  available. The code path, retry logic, schema validation, and flagging are all
  real.
- For offline/demo runs where no API key is available, pre-generated metadata JSON
  files (created via Gemini Chat, which has no quota restrictions) can be placed in
  `corpus/<filename>.json` alongside each image. A small shim in `BatchVisionJob`
  reads these files instead of calling the API, runs the same Pydantic validation,
  and inserts into the DB through the same pipeline that would run against a live API.
- This is noted in `BUILDLOG.md` (here) and the README limitations section so
  reviewers are aware of the mock path.
