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


def _mock_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


@pytest.fixture
def vision_service() -> VisionService:
    with patch("app.core.vision.genai.GenerativeModel"):
        return VisionService()


@pytest.fixture
def fake_image(tmp_path):
    from PIL import Image as PILImage

    path = tmp_path / "fox1.jpg"
    PILImage.new("RGB", (10, 10)).save(path)
    return str(path)


def test_valid_response_accepted(vision_service, fake_image):
    vision_service._model.generate_content = MagicMock(
        return_value=_mock_response(VALID_JSON)
    )
    tag = vision_service.classify_image(fake_image)
    assert isinstance(tag, ImageTag)
    assert tag.subject == "red fox"
    assert tag.confidence == 0.95


def test_invalid_json_retried(vision_service, fake_image):
    vision_service._model.generate_content = MagicMock(
        return_value=_mock_response("not valid json")
    )
    with pytest.raises(VisionError):
        vision_service.classify_image(fake_image)
    assert vision_service._model.generate_content.call_count == 3


def test_low_confidence_flagged(vision_service, fake_image):
    low_conf_json = json.dumps({
        "subject": "unknown animal",
        "category": "unknown",
        "attributes": [],
        "caption": "An unclear image of an animal.",
        "confidence": 0.60,
    })
    vision_service._model.generate_content = MagicMock(
        return_value=_mock_response(low_conf_json)
    )
    tag = vision_service.classify_image(fake_image)
    assert vision_service.is_flagged(tag) is True


def test_high_confidence_not_flagged(vision_service, fake_image):
    vision_service._model.generate_content = MagicMock(
        return_value=_mock_response(VALID_JSON)
    )
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
