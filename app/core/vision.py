import io
import json
import os

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.schemas.image_schema import ImageTag

MAX_RETRIES = 3


class VisionError(Exception):
    """Raised when the vision model fails to produce schema-valid output after retries."""


def _client() -> genai.Client:
    return genai.Client(api_key=settings.GEMINI_API_KEY)


class VisionService:
    def __init__(self) -> None:
        self.last_cost_micro = 0

    def _build_prompt(self) -> str:
        return (
            "You are an image understanding system. Look at the image and "
            "respond with ONLY a JSON object matching exactly this schema, "
            "no markdown, no extra text:\n"
            '{"subject": "main subject e.g. red fox", '
            '"category": "one of: animal landscape food person vehicle building plant object unknown", '
            '"attributes": ["visual", "traits"], '
            '"caption": "one sentence description", '
            '"confidence": 0.95}'
            "\nIf unsure, use category 'unknown' and low confidence."
        )

    def _load_from_json(self, image_path: str) -> ImageTag | None:
        """
        Read pre-generated metadata JSON alongside the image.
        e.g. corpus/fox1.jpg -> corpus/fox1.json
        Same Pydantic validation as live API. Approved by FlyRank support.
        """
        json_path = os.path.splitext(image_path)[0] + ".json"
        if not os.path.exists(json_path):
            return None
        try:
            with open(json_path) as f:
                data = json.load(f)
            return ImageTag.model_validate(data)
        except (ValidationError, json.JSONDecodeError):
            return None

    def _call_api(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """Call Gemini vision API and return raw response text."""
        client = _client()
        response = client.models.generate_content(
            model=settings.VISION_MODEL,
            contents=[
                types.Part.from_text(text=self._build_prompt()),
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response.text

    def classify_image(self, image_path: str) -> ImageTag:
        # JSON fallback first (pre-generated metadata, no API quota needed)
        tag = self._load_from_json(image_path)
        if tag is not None:
            self.last_cost_micro = 0
            return tag

        # Live API path
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                text = self._call_api(image_bytes, mime_type)
                self.last_cost_micro = 0
                return ImageTag.model_validate_json(text)
            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                continue

        raise VisionError(
            f"Vision model failed after {MAX_RETRIES} attempts: {last_error}"
        )

    def is_flagged(self, tag: ImageTag) -> bool:
        return tag.confidence < settings.CONFIDENCE_THRESHOLD
