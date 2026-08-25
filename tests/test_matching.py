import math
from unittest.mock import MagicMock

import pytest

from app.config import settings
from app.core.guard import MismatchGuard
from app.core.matching import MatchingEngine
from app.models.models import Image, Post


def _img(id_, subject, category, is_flagged, embedding):
    img = MagicMock(spec=Image)
    img.id = id_
    img.subject = subject
    img.category = category
    img.is_flagged = is_flagged
    img.embedding = embedding
    img.caption = subject
    img.confidence = 0.95 if not is_flagged else 0.5
    return img


def _post(id_, content, embedding):
    p = MagicMock(spec=Post)
    p.id = id_
    p.content = content
    p.embedding = embedding
    return p


def _unit_vec(dim, *hot):
    """Create a unit-length vector with 1.0 at specified dims and 0 elsewhere."""
    v = [0.0] * dim
    for i in hot:
        v[i] = 1.0
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


DIM = 6
FOX_EMB = _unit_vec(DIM, 0)
WOLF_EMB = _unit_vec(DIM, 1)
DOG_EMB = _unit_vec(DIM, 2)
FOX_POST_EMB = _unit_vec(DIM, 0)   # identical to fox → similarity=1.0
LOW_SIM_EMB = _unit_vec(DIM, 5)   # unrelated → similarity ≈ 0


def _make_engine(post, images):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = post
    db.query.return_value.filter.return_value.all.return_value = images
    engine = MatchingEngine(db=db)
    # Override get_image_candidates to avoid SQLAlchemy filter on ARRAY
    engine.get_image_candidates = lambda pid: sorted(
        [{"image": img, "score": sum(a * b for a, b in zip(post.embedding, img.embedding))} for img in images],
        key=lambda c: c["score"],
        reverse=True,
    )[:10]
    return engine


def test_fox_post_ranks_fox_first():
    fox_img = _img(1, "red fox", "animal", False, FOX_EMB)
    wolf_img = _img(2, "gray wolf", "animal", False, WOLF_EMB)
    dog_img = _img(3, "dog", "animal", False, DOG_EMB)
    post = _post(1, "The behavior of red foxes in the wild.", FOX_POST_EMB)
    engine = _make_engine(post, [fox_img, wolf_img, dog_img])
    result = engine.rank_and_guard(1)
    assert result["suggested"] is not None
    assert result["suggested"]["image"].subject == "red fox"


def test_wolf_rejected_for_fox_post():
    wolf_img = _img(2, "gray wolf", "animal", False, FOX_EMB)  # high sim, wrong subject
    post = _post(1, "The behavior of red foxes in the wild.", FOX_POST_EMB)
    engine = _make_engine(post, [wolf_img])
    result = engine.rank_and_guard(1)
    assert result["suggested"] is None
    rejected_reason = result["rejected"][0]["reason"]
    assert "mismatch" in rejected_reason.lower() or "wolf" in rejected_reason.lower()


def test_low_similarity_rejected():
    img = _img(1, "red fox", "animal", False, LOW_SIM_EMB)
    post = _post(1, "The behavior of red foxes in the wild.", FOX_POST_EMB)
    engine = _make_engine(post, [img])
    result = engine.rank_and_guard(1)
    assert result["suggested"] is None
    assert result["rejected"]
    assert "threshold" in result["rejected"][0]["reason"].lower()


def test_flagged_image_rejected():
    img = _img(1, "red fox", "animal", True, FOX_EMB)  # flagged, high sim
    post = _post(1, "The behavior of red foxes in the wild.", FOX_POST_EMB)
    engine = _make_engine(post, [img])
    result = engine.rank_and_guard(1)
    assert result["suggested"] is None
    assert "human review" in result["rejected"][0]["reason"].lower()


def test_no_match_when_all_rejected():
    imgs = [
        _img(1, "gray wolf", "animal", False, FOX_EMB),
        _img(2, "bear", "animal", False, FOX_EMB),
    ]
    post = _post(1, "The behavior of red foxes in the wild.", FOX_POST_EMB)
    engine = _make_engine(post, imgs)
    result = engine.rank_and_guard(1)
    assert result["no_match"] is True
    assert result["explanation"]


def test_semantic_match_vulpes():
    """Vulpes vulpes (scientific name) post should match red fox image via embedding similarity."""
    fox_img = _img(1, "red fox", "animal", False, FOX_EMB)
    post = _post(1, "Vulpes vulpes hunting at dusk.", FOX_POST_EMB)
    engine = _make_engine(post, [fox_img])
    result = engine.rank_and_guard(1)
    # guard will pass because the embedding similarity is 1.0 and no fox keyword needed
    assert result["suggested"] is not None
    assert result["suggested"]["image"].subject == "red fox"
