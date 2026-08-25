from dataclasses import dataclass

from app.config import settings
from app.models.models import Image, Post

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "fox": ["fox", "vulpes"],
    "wolf": ["wolf", "wolves", "canis lupus"],
    "dog": ["dog", "canine", "puppy", "companion"],
    "bear": ["bear", "hibernat", "ursus"],
    "deer": ["deer", "white-tailed", "fawn", "stag"],
}


@dataclass
class GuardResult:
    passed: bool
    reason: str


def category_mismatch(post_content: str, image_category: str, image_subject: str) -> tuple[bool, str | None]:
    """Return (mismatch, expected_subject) using keyword heuristics on post content."""
    text = post_content.lower()
    image_subject_lower = image_subject.lower()

    matched_keys = [key for key, kws in CATEGORY_KEYWORDS.items() if any(kw in text for kw in kws)]
    if not matched_keys:
        return False, None

    if any(key in image_subject_lower for key in matched_keys):
        return False, None

    return True, matched_keys[0]


class MismatchGuard:
    def check(self, post: Post, image: Image, similarity: float) -> GuardResult:
        if similarity < settings.SIMILARITY_THRESHOLD:
            return GuardResult(
                passed=False,
                reason=f"Similarity {similarity:.2f} below threshold {settings.SIMILARITY_THRESHOLD}",
            )

        if image.is_flagged:
            return GuardResult(
                passed=False,
                reason="Image confidence below threshold — requires human review",
            )

        mismatch, expected = category_mismatch(post.content, image.category, image.subject)
        if mismatch:
            return GuardResult(
                passed=False,
                reason=f"Category mismatch: post expects {expected}, image is {image.subject}",
            )

        return GuardResult(
            passed=True,
            reason=f"Similarity {similarity:.2f} meets threshold, image not flagged, category matches",
        )
