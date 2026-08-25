from datetime import datetime

from pydantic import BaseModel, Field


class ProcessImagesRequest(BaseModel):
    image_dir: str = "./corpus"


class ProcessImagesResponse(BaseModel):
    status: str
    total_images: int


class ImageOut(BaseModel):
    id: int
    filename: str
    subject: str
    category: str
    attributes: list[str]
    caption: str
    confidence: float
    is_flagged: bool

    model_config = {"from_attributes": True}


class SuggestionItem(BaseModel):
    suggestion_id: int
    image: ImageOut
    similarity_score: float
    guard_passed: bool
    reason: str


class PostImagesResponse(BaseModel):
    post_id: int
    suggested: SuggestionItem | None
    rejected: list[SuggestionItem]
    no_match: bool
    explanation: str


class SuggestionOut(BaseModel):
    id: int
    post_id: int
    image_id: int
    similarity_score: float
    guard_passed: bool
    rejection_reason: str | None
    status: str
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    reason: str = Field(default="")


class ExplainResponse(BaseModel):
    suggestion_id: int
    similarity_score: float
    guard_passed: bool
    guard_reason: str | None
    status: str
    image: ImageOut
    tags: dict


class CostEntry(BaseModel):
    id: int
    filename: str | None
    attempt: int
    status: str
    error_message: str | None
    cost_micro: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CostSummary(BaseModel):
    total_entries: int
    by_status: dict[str, int]
    entries: list[CostEntry]
