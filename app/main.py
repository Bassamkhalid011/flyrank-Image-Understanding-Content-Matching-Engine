from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models.models import Base, Post

SAMPLE_POSTS = [
    ("The behavior of red foxes in the wild", "A look at red fox hunting and denning behavior."),
    ("Gray wolves: apex predators of the forest", "How wolf packs hunt and defend territory."),
]


def _seed_sample_posts(db: Session) -> None:
    if db.query(Post).count() > 0:
        return
    for title, content in SAMPLE_POSTS:
        db.add(Post(title=title, content=content))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_sample_posts(db)
    finally:
        db.close()
    yield


app = FastAPI(title="AI Image Understanding & Content Matching Engine", lifespan=lifespan)

from app.api.routes import router  # noqa: E402

app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
