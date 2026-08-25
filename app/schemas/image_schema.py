from pydantic import BaseModel, Field, field_validator

KNOWN_CATEGORIES = {
    "animal",
    "landscape",
    "food",
    "person",
    "vehicle",
    "building",
    "plant",
    "object",
    "unknown",
}


class ImageTag(BaseModel):
    subject: str
    category: str
    attributes: list[str] = Field(default_factory=list)
    caption: str
    confidence: float

    @field_validator("subject", "caption")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @field_validator("category")
    @classmethod
    def category_known(cls, v: str) -> str:
        if v not in KNOWN_CATEGORIES:
            return "unknown"
        return v
