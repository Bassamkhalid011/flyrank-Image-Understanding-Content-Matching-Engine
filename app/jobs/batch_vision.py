import os

from sqlalchemy.orm import Session

from app.core.embeddings import EmbeddingService
from app.core.vision import VisionError, VisionService
from app.models.models import Image, VisionJobLog

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
MAX_RETRIES = 3


class BatchVisionJob:
    def __init__(self, db: Session, vision: VisionService | None = None,
                 embeddings: EmbeddingService | None = None) -> None:
        self.db = db
        self.vision = vision or VisionService()
        self.embeddings = embeddings or EmbeddingService()

    def _already_processed(self, filename: str) -> bool:
        return self.db.query(Image).filter(Image.filename == filename).first() is not None

    def _process_one(self, filename: str, path: str) -> tuple[str, int, str | None]:
        """Returns (status, attempts_used, error_message)."""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                tag = self.vision.classify_image(path)
                embedding = self.embeddings.embed_text(tag.caption)
                is_flagged = self.vision.is_flagged(tag)
                cost_micro = self.vision.last_cost_micro + self.embeddings.last_cost_micro

                image = Image(
                    filename=filename,
                    subject=tag.subject,
                    category=tag.category,
                    attributes=tag.attributes,
                    caption=tag.caption,
                    confidence=tag.confidence,
                    embedding=embedding,
                    is_flagged=is_flagged,
                    cost_micro=cost_micro,
                )
                self.db.add(image)
                self.db.flush()

                status = "flagged" if is_flagged else "success"
                self.db.add(VisionJobLog(
                    image_id=image.id, filename=filename, attempt=attempt,
                    status=status, cost_micro=cost_micro,
                ))
                self.db.commit()
                return status, attempt, None
            except VisionError as exc:
                last_error = str(exc)
                continue

        self.db.add(VisionJobLog(
            image_id=None, filename=filename, attempt=MAX_RETRIES,
            status="failed", error_message=last_error, cost_micro=0,
        ))
        self.db.commit()
        return "failed", MAX_RETRIES, last_error

    def process_all_images(self, image_dir: str) -> dict:
        files = sorted(
            f for f in os.listdir(image_dir) if f.lower().endswith(IMAGE_EXTENSIONS)
        )
        total = len(files)
        counts = {"processed": 0, "flagged": 0, "failed": 0, "skipped": 0}
        total_cost_micro = 0

        for i, filename in enumerate(files, start=1):
            if self._already_processed(filename):
                print(f"Skipping {i}/{total}: {filename} (already processed)")
                counts["skipped"] += 1
                continue

            print(f"Processing {i}/{total}: {filename}...")
            path = os.path.join(image_dir, filename)
            status, attempts, error_message = self._process_one(filename, path)

            if status == "failed":
                counts["failed"] += 1
                print(f"  Failed after {attempts} attempts: {error_message}")
            else:
                counts["processed"] += 1
                if status == "flagged":
                    counts["flagged"] += 1
                image = self.db.query(Image).filter(Image.filename == filename).first()
                total_cost_micro += image.cost_micro if image else 0

        print(
            f"Cost summary: {counts['processed']} processed "
            f"({counts['flagged']} flagged), {counts['failed']} failed, "
            f"{counts['skipped']} skipped, total cost = {total_cost_micro} micro-units"
        )

        return {"total": total, "total_cost_micro": total_cost_micro, **counts}
