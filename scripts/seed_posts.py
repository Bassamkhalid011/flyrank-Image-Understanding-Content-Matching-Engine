"""
Insert sample blog posts into the database and generate embeddings for each.

Usage:
    python scripts/seed_posts.py

Requires DATABASE_URL and GEMINI_API_KEY set (via .env or environment).
Existing posts with the same title are skipped.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.embeddings import EmbeddingService
from app.db.session import SessionLocal
from app.models.models import Base, Post
from app.db.session import engine

POSTS = [
    ("The behavior of red foxes in the wild",
     "Red foxes (Vulpes vulpes) are highly adaptable hunters. They stalk prey "
     "silently through forests and meadows, pouncing on rodents. Their orange "
     "fur blends with autumn leaves, and they den in burrows."),
    ("Gray wolves: apex predators of the forest",
     "The gray wolf (Canis lupus) hunts in coordinated packs. They can bring "
     "down elk and deer through endurance and teamwork. Wolf packs defend "
     "territory with howling and scent marking."),
    ("Domestic dogs as family companions",
     "Dogs have been bred for millennia to live alongside humans. They provide "
     "companionship, protection, and emotional support. Popular breeds include "
     "Labrador retrievers, German shepherds, and beagles."),
    ("Brown bears and their hibernation patterns",
     "Brown bears (Ursus arctos) enter a deep winter sleep called torpor. They "
     "build up fat reserves in autumn by consuming salmon, berries, and roots. "
     "Cubs are born during winter in dens."),
    ("White-tailed deer migration habits",
     "White-tailed deer (Odocoileus virginianus) undertake seasonal migrations "
     "following food availability. Bucks grow and shed antlers annually. Fawns "
     "are born spotted in spring and summer."),
    ("Fox cubs: learning to hunt in the wild",
     "Red fox cubs leave the den at four to five weeks old and begin to learn "
     "hunting skills. They play-fight to develop coordination, and their mother "
     "brings live prey to teach them stalking."),
    ("Wolves and the balance of the Yellowstone ecosystem",
     "When wolves were reintroduced to Yellowstone in 1995, they changed river "
     "courses through trophic cascades. By reducing overgrazing deer herds, "
     "riverbanks regrew vegetation and stabilised."),
    ("Choosing the right dog breed for families",
     "Different breeds suit different lifestyles. High-energy dogs like border "
     "collies need daily runs, while low-energy bulldogs are happy with short "
     "walks. Temperament and shedding are key selection factors."),
    ("Bear safety in the backcountry",
     "Hikers in bear country should carry bear spray and make noise on trails. "
     "Food must be stored in bear canisters. If a brown bear charges, stand "
     "firm — it is usually a bluff charge."),
    ("Deer antler growth and the velvet phase",
     "Deer antlers are the fastest-growing tissue in the animal kingdom. During "
     "summer they are covered in velvet, a soft skin supplying blood. Bucks "
     "rub antlers on trees to remove velvet before the rut."),
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    embedding_svc = EmbeddingService()
    added = 0
    skipped = 0

    for title, content in POSTS:
        existing = db.query(Post).filter(Post.title == title).first()
        if existing:
            print(f"Skipping (exists): {title[:60]}")
            skipped += 1
            continue

        print(f"Embedding: {title[:60]}...")
        try:
            embedding = embedding_svc.embed_text(content)
        except Exception as exc:
            print(f"  Warning: embedding failed — {exc}. Storing without embedding.")
            embedding = None

        post = Post(title=title, content=content, embedding=embedding)
        db.add(post)
        db.commit()
        added += 1

    print(f"\nDone: added {added} posts, skipped {skipped}")
    db.close()


if __name__ == "__main__":
    main()
