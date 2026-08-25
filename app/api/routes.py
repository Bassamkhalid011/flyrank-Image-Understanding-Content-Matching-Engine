import os
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.matching import MatchingEngine
from app.db.session import get_db
from app.models.models import Image, ImageSuggestion, VisionJobLog
from app.schemas.schemas import (
    CostSummary,
    ExplainResponse,
    ImageOut,
    PostImagesResponse,
    ProcessImagesRequest,
    ProcessImagesResponse,
    RejectRequest,
    SuggestionItem,
    SuggestionOut,
)

router = APIRouter()


def _run_batch(image_dir: str) -> None:
    from app.core.embeddings import EmbeddingService
    from app.core.vision import VisionService
    from app.db.session import SessionLocal
    from app.jobs.batch_vision import BatchVisionJob

    db = SessionLocal()
    try:
        job = BatchVisionJob(db=db, vision=VisionService(), embeddings=EmbeddingService())
        job.process_all_images(image_dir)
    finally:
        db.close()


@router.post("/images/process", response_model=ProcessImagesResponse)
def process_images(
    req: ProcessImagesRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ProcessImagesResponse:
    if not os.path.isdir(req.image_dir):
        raise HTTPException(status_code=400, detail=f"Directory not found: {req.image_dir}")
    image_exts = (".jpg", ".jpeg", ".png")
    total = sum(
        1 for f in os.listdir(req.image_dir) if f.lower().endswith(image_exts)
    )
    background_tasks.add_task(_run_batch, req.image_dir)
    return ProcessImagesResponse(status="started", total_images=total)


@router.get("/posts/{post_id}/images", response_model=PostImagesResponse)
def get_images_for_post(post_id: int, db: Session = Depends(get_db)) -> PostImagesResponse:
    engine = MatchingEngine(db=db)
    result = engine.rank_and_guard(post_id)

    def _save_and_build(entry: dict, guard_passed: bool) -> SuggestionItem:
        image: Image = entry["image"]
        suggestion = ImageSuggestion(
            post_id=post_id,
            image_id=image.id,
            similarity_score=entry["score"],
            guard_passed=guard_passed,
            rejection_reason=None if guard_passed else entry["reason"],
            status="pending",
        )
        db.add(suggestion)
        db.flush()
        db.refresh(suggestion)
        return SuggestionItem(
            suggestion_id=suggestion.id,
            image=ImageOut.model_validate(image),
            similarity_score=entry["score"],
            guard_passed=guard_passed,
            reason=entry["reason"],
        )

    suggested_item = None
    rejected_items = []
    if result["suggested"]:
        suggested_item = _save_and_build(result["suggested"], True)
    for entry in result["rejected"]:
        rejected_items.append(_save_and_build(entry, False))
    db.commit()

    return PostImagesResponse(
        post_id=post_id,
        suggested=suggested_item,
        rejected=rejected_items,
        no_match=result["no_match"],
        explanation=result["explanation"],
    )


@router.post("/suggestions/{suggestion_id}/approve", response_model=SuggestionOut)
def approve_suggestion(suggestion_id: int, db: Session = Depends(get_db)) -> SuggestionOut:
    suggestion = db.query(ImageSuggestion).filter(ImageSuggestion.id == suggestion_id).first()
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.status = "approved"
    suggestion.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(suggestion)
    return SuggestionOut.model_validate(suggestion)


@router.post("/suggestions/{suggestion_id}/reject", response_model=SuggestionOut)
def reject_suggestion(
    suggestion_id: int, req: RejectRequest, db: Session = Depends(get_db)
) -> SuggestionOut:
    suggestion = db.query(ImageSuggestion).filter(ImageSuggestion.id == suggestion_id).first()
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.status = "rejected"
    suggestion.reviewed_at = datetime.now(timezone.utc)
    if req.reason:
        suggestion.rejection_reason = req.reason
    db.commit()
    db.refresh(suggestion)
    return SuggestionOut.model_validate(suggestion)


@router.get("/suggestions/{suggestion_id}/explain", response_model=ExplainResponse)
def explain_suggestion(suggestion_id: int, db: Session = Depends(get_db)) -> ExplainResponse:
    suggestion = db.query(ImageSuggestion).filter(ImageSuggestion.id == suggestion_id).first()
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    image = db.query(Image).filter(Image.id == suggestion.image_id).first()
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return ExplainResponse(
        suggestion_id=suggestion.id,
        similarity_score=suggestion.similarity_score,
        guard_passed=suggestion.guard_passed,
        guard_reason=suggestion.rejection_reason,
        status=suggestion.status,
        image=ImageOut.model_validate(image),
        tags={
            "subject": image.subject,
            "category": image.category,
            "attributes": image.attributes,
            "caption": image.caption,
            "confidence": image.confidence,
        },
    )


@router.get("/jobs/costs", response_model=CostSummary)
def get_costs(db: Session = Depends(get_db)) -> CostSummary:
    from collections import Counter
    from app.schemas.schemas import CostEntry

    logs = db.query(VisionJobLog).order_by(VisionJobLog.id).all()
    counter = Counter(log.status for log in logs)
    return CostSummary(
        total_entries=len(logs),
        by_status=dict(counter),
        entries=[CostEntry.model_validate(log) for log in logs],
    )
