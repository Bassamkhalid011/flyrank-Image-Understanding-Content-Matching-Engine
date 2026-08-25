import numpy as np
from google import genai

from app.config import settings


def _client() -> genai.Client:
    return genai.Client(api_key=settings.GEMINI_API_KEY)


class EmbeddingService:
    def __init__(self) -> None:
        self.last_cost_micro = 0

    def embed_text(self, text: str) -> list[float]:
        client = _client()
        result = client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=text,
        )
        self.last_cost_micro = 0  # free tier
        return list(result.embeddings[0].values)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
