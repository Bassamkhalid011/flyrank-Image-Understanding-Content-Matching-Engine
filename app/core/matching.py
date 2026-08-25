from sqlalchemy.orm import Session

from app.core.embeddings import cosine_similarity
from app.core.guard import MismatchGuard
from app.models.models import Image, Post

TOP_K = 10


class MatchingEngine:
    def __init__(self, db: Session, guard: MismatchGuard | None = None) -> None:
        self.db = db
        self.guard = guard or MismatchGuard()

    def get_image_candidates(self, post_id: int) -> list[dict]:
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if post is None or post.embedding is None:
            return []

        images = [img for img in self.db.query(Image).all() if img.embedding is not None]
        scored = [
            {"image": image, "score": cosine_similarity(post.embedding, image.embedding)}
            for image in images
        ]
        scored.sort(key=lambda c: c["score"], reverse=True)
        return scored[:TOP_K]

    def rank_and_guard(self, post_id: int) -> dict:
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if post is None:
            return {
                "suggested": None,
                "rejected": [],
                "no_match": True,
                "explanation": f"No post found with id {post_id}",
            }

        candidates = self.get_image_candidates(post_id)
        if not candidates:
            return {
                "suggested": None,
                "rejected": [],
                "no_match": True,
                "explanation": "No embedded images available to match against",
            }

        suggested = None
        rejected = []
        for candidate in candidates:
            image = candidate["image"]
            score = candidate["score"]
            result = self.guard.check(post, image, score)
            entry = {"image": image, "score": score, "reason": result.reason}
            if result.passed and suggested is None:
                suggested = entry
            else:
                rejected.append(entry)

        if suggested is None:
            explanation = (
                "No candidate image passed the mismatch guard — "
                f"best score was {candidates[0]['score']:.2f}"
            )
        else:
            explanation = f"Top match accepted: {suggested['reason']}"

        return {
            "suggested": suggested,
            "rejected": rejected,
            "no_match": suggested is None,
            "explanation": explanation,
        }
