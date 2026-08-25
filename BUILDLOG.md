# Build Log

Honest record of what AI (Claude) generated, where it was wrong, and what the
developer (Hanzala) had to debug and solve — including major problems encountered.

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

**Claude helped:** `run_eval.py` structure.

**What was wrong / changed:**
- Unsplash Source API returns 503 (deprecated). Wikimedia URLs failed due to no
  internet access on the machine. Picsum.photos also failed (DNS resolution error).
  Resolved by generating images locally with PIL (`scripts/generate_corpus.py`).

---

## MAJOR PROBLEM: Gemini API Key & SDK Issues (solved by developer)

This was the biggest obstacle in the entire capstone. The developer (Hanzala) spent
significant time debugging this personally.

### Problem 1 — Free tier quota is 0 on new accounts
Gemini free tier showed 0 quota for `gemini-2.0-flash` on new API keys. The daily
limit of 1,500 requests was not accessible. This is confirmed in a FlyRank support
ticket (answered 8/6/2026) — the support team acknowledged the issue and approved
the JSON-fallback approach.

### Problem 2 — Google AI Studio now issues OAuth-style keys
Google AI Studio now generates keys starting with `AQ.Ab8R...` instead of the
classic `AIza...` format. This confused the setup process because:
- The key looked wrong (not matching documented format)
- The old `google-generativeai` SDK does not support these OAuth-style keys
- `genai.configure(api_key=...)` with an `AQ.` key raises errors

**How the developer solved it:**
- Hanzala tested the key directly in PowerShell, confirming it connected to Google
  servers (got a 404 on wrong model, not an auth error)
- Identified that the error was wrong model name, not a bad key
- Ran `client.models.list()` to discover the actual available models:
  - Embedding: `gemini-embedding-001` (3072-dim)
  - Vision: `gemini-2.5-flash`
- Confirmed embeddings work: `Works! Length: 3072`

### Problem 3 — Wrong SDK (google-generativeai vs google-genai)
The project was originally built with `google-generativeai` (deprecated). The new
OAuth-style keys and new models only work with `google-genai` (new SDK).

**Fix:** Upgraded the entire codebase to use `google-genai`:
- `app/core/embeddings.py` — rewrote to use `genai.Client` + `client.models.embed_content`
- `app/core/vision.py` — rewrote to use `client.models.generate_content` with
  `types.Part.from_bytes` (PIL Image passing via bytes, not object)
- `app/config.py` — updated model names to `gemini-2.5-flash` and `gemini-embedding-001`
- `tests/test_vision.py` — updated mocks to patch `_call_api` directly instead of
  the old `genai.GenerativeModel`
- `requirements.txt` — added `google-genai`

### Problem 4 — No internet on machine for image downloads
Unsplash, Wikimedia, and Picsum all failed with DNS resolution errors. Solved by:
1. Generating 50 placeholder images locally with PIL (`scripts/generate_corpus.py`)
2. Generating pre-defined JSON metadata for each image (`scripts/generate_metadata_json.py`)
3. The `VisionService._load_from_json()` reads these files, runs the same Pydantic
   validation, and inserts through the same DB pipeline as a live API call would

This approach was explicitly approved by FlyRank support:
> "generate the responses manually through Gemini chat, store them in a JSON file,
> and mock the LLM call in your code. That's completely fine for this capstone —
> it keeps the rest of your pipeline real and testable."

---

## Summary

The core pipeline (embedding, matching, guard, API, tests) was built correctly on
the first pass. The majority of debugging time was spent on the Gemini API key
format change and SDK deprecation — a real-world infrastructure problem that required
the developer to diagnose connection errors, discover available models via API, and
upgrade the entire SDK integration. This is documented honestly here as required.
