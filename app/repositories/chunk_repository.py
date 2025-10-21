"""Chunk repository for managing chunk entities within libraries."""
from typing import Dict, Optional, List
from uuid import UUID
from datetime import datetime
import pickle
from pathlib import Path

from app.domain.models import Chunk, Document, DocumentMetadata
from app.repositories.base_repository import BaseRepository


class ChunkRepository(BaseRepository[Chunk]):
    """Repository for chunk management with thread-safe access and persistence.
    
    Responsibilities:
    - Store and retrieve chunk entities organized by library
    - Manage chunk-to-document relationships
    - Ensure thread-safe concurrent access
    - Persist chunk data to disk
    - Single Responsibility: Chunk data access only
    
    Storage Structure:
        _chunks: Dict[library_id, Dict[chunk_id, chunk]]
        _documents: Dict[library_id, List[Document]]
    """
    
    def __init__(self, persistence_path: Optional[str] = None) -> None:
        """Initialize chunk repository.
        
        Args:
            persistence_path: Optional path to persist chunk data
        """
        super().__init__()
        # Note: For chunks, we need library context, so we store by library_id
        # This is a special case where base repository methods need library_id parameter
        self._chunks: Dict[UUID, Dict[UUID, Chunk]] = {}
        self._documents: Dict[UUID, List[Document]] = {}
        self._persistence_path = persistence_path
        
        print(f"[CHUNK_REPO] 🚀 Initialized ChunkRepository")
        print(f"[CHUNK_REPO] Persistence path: {persistence_path}")
        
        if self._persistence_path:
            self._load_from_disk()
        else:
            print(f"[CHUNK_REPO] ⚠️ Persistence disabled")
    
    # Override base methods to add library_id parameter
    def save(self, entity: Chunk) -> Chunk:
        """Not directly used - use create_chunk_in_library instead."""
        raise NotImplementedError("Use create_chunk_in_library with library_id parameter")
    
    def find_by_id(self, id: UUID) -> Optional[Chunk]:
        """Not directly used - use get_chunk with library_id parameter."""
        raise NotImplementedError("Use get_chunk with library_id parameter")
    
    def find_all(self) -> List[Chunk]:
        """Not directly used - use list_chunks with library_id parameter."""
        raise NotImplementedError("Use list_chunks with library_id parameter")
    
    def delete(self, id: UUID) -> bool:
        """Not directly used - use delete_chunk with library_id parameter."""
        raise NotImplementedError("Use delete_chunk with library_id parameter")
    
    # Chunk-specific methods with library context
    def create_chunk_in_library(self, library_id: UUID, chunk: Chunk) -> Optional[Chunk]:
        """Create a chunk and add it to a library with proper locking.
        
        Args:
            library_id: UUID of the library to add chunk to
            chunk: Chunk entity to create
            
        Returns:
            Created chunk if successful, None if library not found
        """
        with self._lock.write_lock():
            # Initialize library storage if needed
            if library_id not in self._chunks:
                self._chunks[library_id] = {}
            if library_id not in self._documents:
                self._documents[library_id] = []
            
            # Find or create document for this chunk
            document = None
            if chunk.document_id:
                for doc in self._documents[library_id]:
                    if doc.id == chunk.document_id:
                        document = doc
                        break
            
            if not document:
                # Create a new default document
                document = Document(
                    library_id=library_id,
                    metadata=DocumentMetadata(title="Default Document")
                )
                self._documents[library_id].append(document)
                chunk.document_id = document.id
                print(f"[CHUNK_REPO] 📄 Created new document {document.id} for library {library_id}")
            
            # Add chunk to document
            document.chunks.append(chunk)
            document.updated_at = datetime.utcnow()
            
            # Store chunk in lookup dict
            self._chunks[library_id][chunk.id] = chunk
            
            print(f"[CHUNK_REPO] ✅ Created chunk {chunk.id} in library {library_id}")
            
            self._persist()
            return chunk
    
    def get_chunk(self, library_id: UUID, chunk_id: UUID) -> Optional[Chunk]:
        """Retrieve a chunk by ID from a specific library.
        
        Args:
            library_id: UUID of the library
            chunk_id: UUID of the chunk
            
        Returns:
            Chunk if found, None otherwise
        """
        with self._lock.read_lock():
            if library_id not in self._chunks:
                return None
            return self._chunks[library_id].get(chunk_id)
    
    def list_chunks(self, library_id: UUID) -> List[Chunk]:
        """Retrieve all chunks in a library.
        
        Args:
            library_id: UUID of the library
            
        Returns:
            List of all chunks in the library
        """
        with self._lock.read_lock():
            if library_id not in self._chunks:
                return []
            return list(self._chunks[library_id].values())
    
    def update_chunk(self, library_id: UUID, chunk_id: UUID, chunk: Chunk) -> Optional[Chunk]:
        """Update an existing chunk.
        
        Args:
            library_id: UUID of the library
            chunk_id: UUID of the chunk to update
            chunk: Updated chunk object
            
        Returns:
            Updated chunk if found, None otherwise
        """
        with self._lock.write_lock():
            if library_id not in self._chunks:
                return None
            if chunk_id not in self._chunks[library_id]:
                return None
            
            # Update chunk in storage
            self._chunks[library_id][chunk_id] = chunk
            
            # Update chunk in document
            for document in self._documents.get(library_id, []):
                for i, existing_chunk in enumerate(document.chunks):
                    if existing_chunk.id == chunk_id:
                        document.chunks[i] = chunk
                        document.updated_at = datetime.utcnow()
                        break
            
            print(f"[CHUNK_REPO] 📝 Updated chunk {chunk_id} in library {library_id}")
            
            self._persist()
            return chunk
    
    def delete_chunk(self, library_id: UUID, chunk_id: UUID) -> bool:
        """Delete a chunk by ID from a library.
        
        Args:
            library_id: UUID of the library
            chunk_id: UUID of the chunk to delete
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock.write_lock():
            if library_id not in self._chunks:
                return False
            if chunk_id not in self._chunks[library_id]:
                return False
            
            # Remove from storage
            del self._chunks[library_id][chunk_id]
            
            # Remove from document
            for document in self._documents.get(library_id, []):
                for chunk in document.chunks:
                    if chunk.id == chunk_id:
                        document.chunks.remove(chunk)
                        document.updated_at = datetime.utcnow()
                        break
            
            print(f"[CHUNK_REPO] 🗑️ Deleted chunk {chunk_id} from library {library_id}")
            
            self._persist()
            return True
    
    def get_documents_for_library(self, library_id: UUID) -> List[Document]:
        """Get all documents in a library (for index rebuilding).
        
        Args:
            library_id: UUID of the library
            
        Returns:
            List of documents in the library
        """
        with self._lock.read_lock():
            return self._documents.get(library_id, [])
    
    def _persist(self) -> None:
        """Persist chunk data to disk."""
        if not self._persistence_path:
            return
        
        try:
            # Ensure persistence_path is treated as a directory
            base_path = Path(self._persistence_path)
            if base_path.suffix == '.pkl':
                # Remove .pkl extension if present (legacy compatibility)
                base_path = base_path.with_suffix('')
            
            # Create directory if it doesn't exist
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Save to chunks.pkl inside the directory
            path = base_path / "chunks.pkl"
            
            # Atomic write pattern
            temp_path = path.with_suffix('.tmp')
            
            with open(temp_path, 'wb') as f:
                pickle.dump({
                    'chunks': self._chunks,
                    'documents': self._documents
                }, f)
            
            # Atomic rename
            temp_path.replace(path)
            
        except Exception as e:
            print(f"[CHUNK_REPO] ❌ Error persisting chunks: {e}")
    
    def _load_from_disk(self) -> None:
        """Load chunk data from disk."""
        if not self._persistence_path:
            return
        
        try:
            # Ensure persistence_path is treated as a directory
            base_path = Path(self._persistence_path)
            if base_path.suffix == '.pkl':
                # Remove .pkl extension if present (legacy compatibility)
                base_path = base_path.with_suffix('')
            
            path = base_path / "chunks.pkl"
            if not path.exists():
                print(f"[CHUNK_REPO] No persistence file found at {path}")
                return
            
            print(f"[CHUNK_REPO] 📂 Loading chunks from {path}")
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self._chunks = data.get('chunks', {})
                self._documents = data.get('documents', {})
            
            total_chunks = sum(len(chunks) for chunks in self._chunks.values())
            print(f"[CHUNK_REPO] ✅ Loaded {total_chunks} chunks across {len(self._chunks)} libraries")
            
        except Exception as e:
            print(f"[CHUNK_REPO] ❌ Error loading chunks: {e}")
            import traceback
            traceback.print_exc()
