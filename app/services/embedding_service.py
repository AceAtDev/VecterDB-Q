"""Turn text into embeddings, with Cohere or a local model.

Both providers return 384-dimension vectors, but they are different models:
a library must be filled and searched with the same provider.
"""
import logging
import threading
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

COHERE_MODEL = "embed-english-light-v3.0"
INPUT_TYPES = ("search_document", "search_query")


class EmbeddingUnavailable(RuntimeError):
    """No embedding provider can be used with the current configuration."""


class EmbeddingService:
    """Embeds text with the configured provider."""

    def __init__(self, provider: str = "auto", cohere_api_key: str = "",
                 local_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if provider == "auto":
            provider = "cohere" if cohere_api_key else "local"
        if provider not in ("cohere", "local"):
            raise ValueError(f"Unknown embedding provider '{provider}' (use auto, cohere or local)")
        self.provider = provider
        self.cohere_api_key = cohere_api_key
        self.local_model_name = local_model
        self._local_model = None
        self._load_lock = threading.Lock()

    @property
    def model_name(self) -> str:
        return COHERE_MODEL if self.provider == "cohere" else self.local_model_name

    def embed(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """Embed texts. input_type matters for Cohere; the local model ignores it."""
        if input_type not in INPUT_TYPES:
            raise ValueError(f"input_type must be one of {INPUT_TYPES}")
        if not texts:
            return []
        if self.provider == "cohere":
            return self._embed_cohere(texts, input_type)
        return self._embed_local(texts)

    def _embed_cohere(self, texts: List[str], input_type: str) -> List[List[float]]:
        if not self.cohere_api_key:
            raise EmbeddingUnavailable("EMBEDDING_PROVIDER is cohere but COHERE_API_KEY is not set")
        response = httpx.post(
            "https://api.cohere.ai/v1/embed",
            headers={"Authorization": f"Bearer {self.cohere_api_key}"},
            json={"texts": texts, "model": COHERE_MODEL, "input_type": input_type},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["embeddings"]

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        model = self._get_local_model()
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def _get_local_model(self):
        # Loaded on first use so the server starts fast and runs without the package
        if self._local_model is None:
            with self._load_lock:
                if self._local_model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                    except ImportError as exc:
                        raise EmbeddingUnavailable(
                            "Local embeddings need sentence-transformers: "
                            "pip install -r requirements-local.txt (or set COHERE_API_KEY)"
                        ) from exc
                    logger.info("Loading local embedding model %s", self.local_model_name)
                    self._local_model = SentenceTransformer(self.local_model_name, device="cpu")
        return self._local_model
