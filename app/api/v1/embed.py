"""Embedding endpoint: turns text into vectors so clients never hold an API key."""
from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.embedding_service import EmbeddingService, EmbeddingUnavailable
from app.api.dependencies import get_embedding_service


router = APIRouter()


class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=96)
    input_type: Literal["search_document", "search_query"] = "search_document"


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    provider: str
    model: str
    dimension: int


@router.post(
    "",
    response_model=EmbedResponse,
    summary="Embed text",
    description="Embed up to 96 texts with the server's provider (Cohere, or a local model when no key is set)."
)
def embed_texts(
    request: EmbedRequest,
    service: EmbeddingService = Depends(get_embedding_service)
) -> EmbedResponse:
    try:
        vectors = service.embed(request.texts, request.input_type)
    except EmbeddingUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return EmbedResponse(
        embeddings=vectors,
        provider=service.provider,
        model=service.model_name,
        dimension=len(vectors[0]),
    )
