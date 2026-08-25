import os
from unittest.mock import MagicMock, patch

import pytest

from app.models.models import Image, ImageSuggestion, Post, VisionJobLog


def _seed_post(db_session, content="The behavior of red foxes in the wild."):
    post = Post(title="Fox post", content=content, embedding=[0.1] * 768)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


def _seed_image(db_session, filename="fox1.jpg", subject="red fox", is_flagged=False,
                embedding=None):
    if embedding is None:
        embedding = [0.1] * 768  # very similar to post
    img = Image(
        filename=filename, subject=subject, category="animal",
        attributes=["orange fur"], caption="A red fox.", confidence=0.95,
        embedding=embedding, is_flagged=is_flagged,
    )
    db_session.add(img)
    db_session.commit()
    db_session.refresh(img)
    return img


def _seed_suggestion(db_session, post_id, image_id, guard_passed=True):
    s = ImageSuggestion(
        post_id=post_id, image_id=image_id, similarity_score=0.90,
        guard_passed=guard_passed,
        rejection_reason=None if guard_passed else "low similarity",
        status="pending",
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def _seed_log(db_session):
    log = VisionJobLog(filename="fox1.jpg", attempt=1, status="success", cost_micro=0)
    db_session.add(log)
    db_session.commit()


def test_process_images_starts_job(client, db_session, tmp_path):
    (tmp_path / "fox1.jpg").write_bytes(b"")
    with patch("app.api.routes._run_batch") as mock_run:
        resp = client.post(
            "/images/process",
            json={"image_dir": str(tmp_path)},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert data["total_images"] == 1


def test_get_images_for_post_returns_ranked_results(client, db_session):
    post = _seed_post(db_session)
    _seed_image(db_session)
    resp = client.get(f"/posts/{post.id}/images")
    assert resp.status_code == 200
    data = resp.json()
    assert "suggested" in data
    assert "no_match" in data


def test_get_images_no_match_returns_explanation(client, db_session):
    # post with no images in DB
    post = _seed_post(db_session, content="Quantum computing advances")
    resp = client.get(f"/posts/{post.id}/images")
    assert resp.status_code == 200
    data = resp.json()
    assert data["no_match"] is True
    assert data["explanation"]


def test_approve_suggestion(client, db_session):
    post = _seed_post(db_session)
    img = _seed_image(db_session)
    s = _seed_suggestion(db_session, post.id, img.id)
    resp = client.post(f"/suggestions/{s.id}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["reviewed_at"] is not None


def test_reject_suggestion_with_reason(client, db_session):
    post = _seed_post(db_session)
    img = _seed_image(db_session)
    s = _seed_suggestion(db_session, post.id, img.id)
    resp = client.post(f"/suggestions/{s.id}/reject", json={"reason": "wrong animal"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["rejection_reason"] == "wrong animal"


def test_explain_suggestion_returns_full_detail(client, db_session):
    post = _seed_post(db_session)
    img = _seed_image(db_session)
    s = _seed_suggestion(db_session, post.id, img.id)
    resp = client.get(f"/suggestions/{s.id}/explain")
    assert resp.status_code == 200
    data = resp.json()
    assert "similarity_score" in data
    assert "guard_passed" in data
    assert "tags" in data
    assert data["tags"]["subject"] == "red fox"


def test_cost_log_has_entries_after_processing(client, db_session):
    _seed_log(db_session)
    resp = client.get("/jobs/costs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_entries"] >= 1
    assert "success" in data["by_status"]
