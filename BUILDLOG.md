# Build Log

Honest record of what AI (Claude) generated, where it was wrong, and what the
developer (Bassam) had to debug and solve — including major problems encountered.

---

## Phase 1 — Design & Scaffold

**Claude helped:** Generated the initial project structure, README architecture
diagram, Docker setup, pydantic-settings config, and SQLAlchemy models.

**What was wrong / changed:**
- The original `Image.embedding` column used SQLAlchemy `ARRAY(Float)` — Postgres-only,
  breaks SQLite test runs. Fixed by writing a custom `Vector` TypeDecorator that
  serialises to JSON text, making it work with both backends.

---

## Phase 2 — Image Understanding Pipeline

**Claude helped:** `VisionService` structure, retry logic, Pydantic schema validation,
and the `response_mime_type="application/json"` pattern to force JSON output.

**What was wrong / changed:**
- Retry counter had an off-by-one; fixed so `VisionError` is always raised after
  exactly `MAX_RETRIES` attempts.
- `BatchVisionJob` had a double-counting bug for failed images; refactored into
  `_process_one` to separate concerns.

---

## Phase 3 — Matching Engine & Mismatch Guard

**Claude helped:** Cosine similarity with numpy, top-K candidate pattern,
MismatchGuard checking three independent rules.

**What was wrong / changed:**
- `category_mismatch` keyword heuristic missed "Vulpes vulpes" as a fox synonym —
  added to keyword list.
- Guard originally short-circuited on first rule; kept checking all rules
  independently as the spec requires.

---

## Phase 4 — API Routes

**Claude helped:** FastAPI route scaffolding, BackgroundTasks usage,
`dependency_overrides` pattern for SQLite in tests.

**What was wrong / changed:**
- First version of `GET /posts/{post_id}/images` did not save `ImageSuggestion` rows.
  Fixed so every candidate (accepted or rejected) is persisted for the review workflow.

---

## Phase 5 — Eval & Scripts

**Claude helped:** `run_eval.py` structure and corpus seeding scripts.

**What was wrong / changed:**
- Unsplash Source API returns 503 (deprecated). Wikimedia and Picsum also failed
  due to no internet access from the script environment.
- Solved by downloading the Kaggle animal image dataset manually and writing
  `scripts/copy_from_kaggle.py` to copy and rename 50 real animal images
  (fox, wolf, dog, bear, deer) into `corpus/` with the correct naming convention.

---

## MAJOR PROBLEM: Gemini API Key & SDK Issues (solved by developer)

This was the biggest obstacle in the entire capstone. Bassam spent significant
time personally debugging and solving this.

### Problem 1 — Free tier quota is 0 on new accounts
Gemini free tier showed 0 quota for `gemini-2.0-flash` on new API keys. This is
confirmed in a FlyRank support ticket (answered 8/6/2026) — the support team
acknowledged the issue.

### Problem 2 — Google AI Studio now issues OAuth-style keys
Google AI Studio now generates keys starting with `AQ.Ab8R...` instead of the
classic `AIza...` format. This caused confusion because:
- The key looked wrong (not matching any documented format)
- The old `google-generativeai` SDK does not support these keys
- `genai.configure(api_key=...)` with an `AQ.` key raises errors

**How Bassam solved it:**
- Tested the key directly in PowerShell, confirmed it connected to Google servers
  (got a 404 on wrong model name — not an auth error, meaning the key was valid)
- Ran `client.models.list()` to discover the actual available models:
  - Embedding: `gemini-embedding-001` (3072-dim vectors)
  - Vision: `gemini-2.5-flash`
- Confirmed embeddings work by running a live test: `Works! Length: 3072`

### Problem 3 — Wrong SDK (google-generativeai vs google-genai)
The project was initially built with `google-generativeai` (now deprecated). The
new OAuth-style keys and updated models only work with `google-genai` (new SDK).

**Fix applied:**
- `app/core/embeddings.py` — rewrote to use `genai.Client` + `client.models.embed_content`
- `app/core/vision.py` — rewrote to use `client.models.generate_content` with
  `types.Part.from_bytes` (image passed as bytes, not PIL object)
- `app/config.py` — updated model names to `gemini-2.5-flash` and `gemini-embedding-001`
- `tests/test_vision.py` — updated mocks to patch `_call_api` directly
- `requirements.txt` — added `google-genai`

### Problem 4 — No internet on machine for automated image downloads
Unsplash, Wikimedia, and Picsum all failed with DNS resolution errors from the
script environment. Bassam solved this by:
- Downloading the Kaggle animal dataset manually
- Writing `scripts/copy_from_kaggle.py` to automatically copy and rename 50 real
  animal images from the dataset into `corpus/` with correct filenames

---

## Summary

The core pipeline (embedding, matching, guard, API, tests) was built correctly on
the first pass. The majority of debugging time was spent on the Gemini API key
format change and SDK deprecation — a real infrastructure problem that required
Bassam to diagnose connection errors, discover available models via the API, and
upgrade the entire SDK integration. All 18 tests pass after the upgrade.
