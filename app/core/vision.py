import json

import google.generativeai as genai
from pydantic import ValidationError

from app.config import settings
from app.schemas.image_schema import ImageTag

MAX_RETRIES = 3


class VisionError(Exception):
    """Raised when the vision model fails to produce schema-valid output after retries."""


class VisionService:
    def __init__(self) -> None:
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.VISION_MODEL)
        self.last_cost_micro = 0

    def _build_prompt(self) -> str:
        return (
            "You are an image understanding system. Look at the image and "
            "respond with ONLY a JSON object matching exactly this schema, "
            "no markdown, no extra text:\n"
            "{\n"
            '  "subject": string,        // the main subject, e.g. "red fox"\n'
            '  "category": string,       // one of: animal, landscape, food, '
            "person, vehicle, building, plant, object, unknown\n"
            '  "attributes": [string],   // notable visual attributes, e.g. '
            '["orange fur", "wild", "forest"]\n'
            '  "caption": string,        // a one-sentence natural language caption\n'
            '  "confidence": float       // your confidence in this classification, 0.0-1.0\n'
            "}\n"
            "If you are unsure of the subject, use category \"unknown\" and a "
            "low confidence score. Never invent a subject you are not "
            "reasonably sure of."
        )

    def classify_image(self, image_path: str) -> ImageTag:
        import PIL.Image

        img = PIL.Image.open(image_path)
        prompt = self._build_prompt()

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._model.generate_content(
                    [prompt, img],
                    generation_config={"response_mime_type": "application/json"},
                )
                self.last_cost_micro = 0  # Gemini Flash free tier = $0
                return ImageTag.model_validate_json(response.text)
            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                continue
            except Exception as exc:  # transport/API errors also retried
                last_error = exc
                continue

        raise VisionError(
            f"Vision model failed to produce schema-valid output after "
            f"{MAX_RETRIES} attempts: {last_error}"
        )

    def is_flagged(self, tag: ImageTag) -> bool:
        return tag.confidence < settings.CONFIDENCE_THRESHOLD
