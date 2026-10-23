"""Domain models for the Vector Database."""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class ChunkMetadata(BaseModel):
    """Metadata for a chunk."""
    source: str = Field(default="unknown", description="Source of the chunk")
    page: Optional[int] = Field(None, description="Page number if applicable")
    section: Optional[str] = Field(None, description="Section name if applicable")
    author: Optional[str] = Field(None, description="Author of the content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")


class Chunk(BaseModel):
    """A chunk represents a piece of text with an associated embedding."""
    
    model_config = ConfigDict(frozen=False)
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    text: str = Field(..., min_length=1, description="The text content of the chunk")
    embedding: List[float] = Field(..., min_length=1, description="Vector embedding")
    metadata: ChunkMetadata = Field(default_factory=lambda: ChunkMetadata(source="unknown"), description="Chunk metadata")
    document_id: Optional[UUID] = Field(None, description="Parent document ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChunkCreate(BaseModel):
    """Schema for creating a new chunk."""
    text: str = Field(..., min_length=1)
    embedding: List[float] = Field(..., min_length=1)
    metadata: ChunkMetadata = Field(default_factory=lambda: ChunkMetadata(source="unknown"))
    document_id: Optional[UUID] = None


class ChunkUpdate(BaseModel):
    """Schema for updating a chunk."""
    text: Optional[str] = Field(None, min_length=1)
    embedding: Optional[List[float]] = Field(None, min_length=1)
    metadata: Optional[ChunkMetadata] = None
    document_id: Optional[UUID] = None


class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    title: str = Field(..., description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    source: Optional[str] = Field(None, description="Document source")
    language: str = Field(default="en", description="Document language")
    category: Optional[str] = Field(None, description="Document category")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class Document(BaseModel):
    """A document is made of multiple chunks."""
    
    model_config = ConfigDict(frozen=False)
    
    id: UUID = Field(default_factory=uuid4)
    chunks: List[Chunk] = Field(default_factory=list)
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    library_id: Optional[UUID] = Field(None, description="Parent library ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LibraryMetadata(BaseModel):
    """Metadata for a library."""
    category: Optional[str] = Field(None, description="Library category")
    language: str = Field(default="en", description="Primary language")
    tags: List[str] = Field(default_factory=list, description="Library tags")
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class Library(BaseModel):
    """A library is a collection of documents."""
    
    model_config = ConfigDict(frozen=False)
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, description="Library name")
    description: Optional[str] = Field(None, description="Library description")
    documents: List[Document] = Field(default_factory=list)
    metadata: LibraryMetadata = Field(default_factory=LibraryMetadata)
    index_type: str = Field(default="flat", description="Type of index used")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LibraryCreate(BaseModel):
    """Schema for creating a library."""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    metadata: LibraryMetadata = Field(default_factory=LibraryMetadata)
    index_type: str = Field(default="flat", pattern="^(flat|ivf)$")


class LibraryUpdate(BaseModel):
    """Schema for updating a library."""
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    metadata: Optional[LibraryMetadata] = None
    index_type: Optional[str] = Field(None, pattern="^(flat|ivf)$")


class SearchQuery(BaseModel):
    """Schema for search queries."""
    embedding: List[float] = Field(..., min_length=1, description="Query embedding vector")
    k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    metric: str = Field(default="euclidean", pattern="^(euclidean|cosine)$", description="Distance metric")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class SearchResult(BaseModel):
    """Schema for search results."""
    chunk: Chunk
    score: float = Field(..., description="Similarity score (cosine similarity)")
    distance: float = Field(..., description="Distance metric")
