import google.generativeai as genai
import numpy as np

from app.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.last_cost_micro = 0

    def embed_text(self, text: str) -> list[float]:
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=text,
            task_type="SEMANTIC_SIMILARITY",
        )
        self.last_cost_micro = 0  # Gemini embeddings free tier = $0
        return result["embedding"]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
