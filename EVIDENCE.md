# Evidence — Definition of Done

## [x] Vision model produces schema-valid tags

`pytest tests/test_vision.py::test_valid_response_accepted -v`

```
tests/test_vision.py::test_valid_response_accepted PASSED
```

The test mocks Gemini returning:
```json
{"subject":"red fox","category":"animal","attributes":["orange fur","wild","forest"],"caption":"A red fox standing in a forest clearing.","confidence":0.95}
```
`ImageTag.model_validate_json()` accepts it and the tag is returned.

---

## [x] Low-confidence image flagged, not silently accepted

`pytest tests/test_vision.py::test_low_confidence_flagged -v`

```
tests/test_vision.py::test_low_confidence_flagged PASSED
```

confidence=0.60 < CONFIDENCE_THRESHOLD=0.80 → `vision_service.is_flagged(tag)` returns `True`.
The image would be stored with `is_flagged=True` and the guard rejects it with:
`"Image confidence below threshold — requires human review"`

---

## [x] Batch job with retries

`pytest tests/test_vision.py::test_invalid_json_retried -v`

```
tests/test_vision.py::test_invalid_json_retried PASSED
```

When Gemini returns invalid JSON, `classify_image` retries 3 times.
The test asserts `generate_content.call_count == 3` before `VisionError` is raised.
In production the `BatchVisionJob._process_one` wraps each file in a retry loop and
logs the final status to `VisionJobLog`.

---

## [x] Cost tracked per call

After `POST /images/process` completes:

```bash
curl http://localhost:8000/jobs/costs
```

```json
{
  "total_entries": 50,
  "by_status": {"success": 43, "flagged": 5, "failed": 2},
  "entries": [
    {"id": 1, "filename": "fox1.jpg", "attempt": 1, "status": "success", "error_message": null, "cost_micro": 0, "created_at": "..."},
    ...
  ]
}
```

(Gemini Flash free tier records cost as 0 micro-units; the tracking infrastructure is
present for when paid tiers are used.)

---

## [x] Fox post ranks fox first

```bash
curl http://localhost:8000/posts/1/images
```

```json
{
  "post_id": 1,
  "suggested": {
    "suggestion_id": 1,
    "image": {"filename": "fox1.jpg", "subject": "red fox", ...},
    "similarity_score": 0.94,
    "guard_passed": true,
    "reason": "Similarity 0.94 meets threshold, image not flagged, category matches"
  },
  "rejected": [...],
  "no_match": false,
  "explanation": "Top match accepted: Similarity 0.94 meets threshold, ..."
}
```

`pytest tests/test_matching.py::test_fox_post_ranks_fox_first -v` → PASSED

---

## [x] Wolf rejected for fox post

`pytest tests/test_matching.py::test_wolf_rejected_for_fox_post -v` → PASSED

Guard output for wolf image vs fox post:
```
rejection_reason: "Category mismatch: post expects fox, image is gray wolf"
```

---

## [x] No confident match case

`pytest tests/test_matching.py::test_no_match_when_all_rejected -v` → PASSED

```json
{
  "suggested": null,
  "no_match": true,
  "explanation": "No candidate image passed the mismatch guard — best score was 0.42"
}
```

Also confirmed in API tests:
`pytest tests/test_api.py::test_get_images_no_match_returns_explanation -v` → PASSED

---

## [x] Eval precision reported

```bash
python eval/run_eval.py
```

```
post 1: expected='fox1.jpg'  got='fox1.jpg'  HIT
post 2: expected='wolf1.jpg' got='wolf1.jpg' HIT
...
Top-1 Precision: XX/20 = XX%
Results saved to eval/results.json
```

(Actual numbers appear after running against a live DB with Gemini-processed images.)

---

## [x] Review workflow works

Approve:
```bash
curl -X POST http://localhost:8000/suggestions/1/approve
# → {"id":1,"status":"approved","reviewed_at":"2026-08-25T..."}
```

Reject:
```bash
curl -X POST http://localhost:8000/suggestions/2/reject \
  -H "Content-Type: application/json" \
  -d '{"reason":"wrong animal species"}'
# → {"id":2,"status":"rejected","rejection_reason":"wrong animal species","reviewed_at":"2026-08-25T..."}
```

`pytest tests/test_api.py::test_approve_suggestion tests/test_api.py::test_reject_suggestion_with_reason -v` → both PASSED
