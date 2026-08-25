import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.core.vision import VisionError, VisionService
from app.schemas.image_schema import ImageTag

VALID_JSON = json.dumps({
    "subject": "red fox",
    "category": "animal",
    "attributes": ["orange fur", "wild", "forest"],
    "caption": "A red fox standing in a forest clearing.",
    "confidence": 0.95,
})


@pytest.fixture
def fake_image(tmp_path):
    from PIL import Image as PILImage
    path = tmp_path / "fox1.jpg"
    PILImage.new("RGB", (10, 10)).save(path)
    return str(path)


@pytest.fixture
def vision_service():
    return VisionService()


def test_valid_response_accepted(vision_service, fake_image):
    with patch.object(vision_service, "_call_api", return_value=VALID_JSON):
        tag = vision_service.classify_image(fake_image)
    assert isinstance(tag, ImageTag)
    assert tag.subject == "red fox"
    assert tag.confidence == 0.95


def test_invalid_json_retried(vision_service, fake_image):
    with patch.object(vision_service, "_call_api", return_value="not valid json"):
        with pytest.raises(VisionError):
            vision_service.classify_image(fake_image)


def test_low_confidence_flagged(vision_service, fake_image):
    low_conf = json.dumps({
        "subject": "unknown animal",
        "category": "unknown",
        "attributes": [],
        "caption": "An unclear image of an animal.",
        "confidence": 0.60,
    })
    with patch.object(vision_service, "_call_api", return_value=low_conf):
        tag = vision_service.classify_image(fake_image)
    assert vision_service.is_flagged(tag) is True


def test_high_confidence_not_flagged(vision_service, fake_image):
    with patch.object(vision_service, "_call_api", return_value=VALID_JSON):
        tag = vision_service.classify_image(fake_image)
    assert vision_service.is_flagged(tag) is False


def test_missing_field_rejected():
    payload = {
        "category": "animal",
        "attributes": [],
        "caption": "A fox.",
        "confidence": 0.9,
    }
    with pytest.raises(ValidationError):
        ImageTag.model_validate(payload)
