"""Vector database repository for managing libraries and their indexes."""
from typing import Dict, List, Optional
from uuid import UUID
import pickle
from pathlib import Path
import numpy as np

from app.domain.models import Library, Chunk
from app.core.locks import RWLock
from app.core.indexes import VectorIndex, FlatIndex, IVFIndex


class VectorDBRepository:
    """Repository for managing vector database operations with thread-safe access."""
    
    def __init__(self, persistence_path: Optional[str] = None) -> None:
        self._libraries: Dict[UUID, Library] = {}
        self._indexes: Dict[UUID, VectorIndex] = {}
        self._lock = RWLock()
        self._persistence_path = persistence_path
        
        if self._persistence_path:
            self._load_from_disk()
    
    def create_library(self, library: Library) -> Library:
        with self._lock.write_lock():
            if library.id in self._libraries:
                raise ValueError(f"Library with ID {library.id} already exists")
            
            self._libraries[library.id] = library
            self._create_index_for_library(library)
            self._persist()
            return library
    
    def get_library(self, library_id: UUID) -> Optional[Library]:
        with self._lock.read_lock():
            return self._libraries.get(library_id)
    
    def list_libraries(self) -> List[Library]:
        with self._lock.read_lock():
            return list(self._libraries.values())
    
    def update_library(self, library_id: UUID, library: Library) -> Optional[Library]:
        with self._lock.write_lock():
            if library_id not in self._libraries:
                return None
            
            old_index_type = self._libraries[library_id].index_type
            if old_index_type != library.index_type:
                self._create_index_for_library(library)
                self._reindex_library(library)
            
            self._libraries[library_id] = library
            self._persist()
            return library
    
    def delete_library(self, library_id: UUID) -> bool:
        with self._lock.write_lock():
            if library_id not in self._libraries:
                return False
            
            del self._libraries[library_id]
            if library_id in self._indexes:
                del self._indexes[library_id]
            
            self._persist()
            return True
    
    def add_chunk_to_library(self, library_id: UUID, chunk: Chunk) -> Optional[Chunk]:
        with self._lock.write_lock():
            library = self._libraries.get(library_id)
            if not library:
                return None
            
            index = self._indexes.get(library_id)
            if index:
                vector = np.array(chunk.embedding)
                index.add(np.array([vector]), [str(chunk.id)])
            
            self._persist()
            return chunk
    
    def get_chunk(self, library_id: UUID, chunk_id: UUID) -> Optional[Chunk]:
        with self._lock.read_lock():
            library = self._libraries.get(library_id)
            if not library:
                return None
            
            for document in library.documents:
                for chunk in document.chunks:
                    if chunk.id == chunk_id:
                        return chunk
            return None
    
    def list_chunks(self, library_id: UUID) -> List[Chunk]:
        with self._lock.read_lock():
            library = self._libraries.get(library_id)
            if not library:
                return []
            
            chunks = []
            for document in library.documents:
                chunks.extend(document.chunks)
            return chunks
    
    def update_chunk(self, library_id: UUID, chunk_id: UUID, chunk: Chunk) -> Optional[Chunk]:
        with self._lock.write_lock():
            library = self._libraries.get(library_id)
            if not library:
                return None
            
            for document in library.documents:
                for i, existing_chunk in enumerate(document.chunks):
                    if existing_chunk.id == chunk_id:
                        document.chunks[i] = chunk
                        
                        index = self._indexes.get(library_id)
                        if index:
                            vector = np.array(chunk.embedding)
                            index.update(str(chunk_id), vector)
                        
                        self._persist()
                        return chunk
            
            return None
    
    def delete_chunk(self, library_id: UUID, chunk_id: UUID) -> bool:
        with self._lock.write_lock():
            library = self._libraries.get(library_id)
            if not library:
                return False
            
            for document in library.documents:
                for chunk in document.chunks:
                    if chunk.id == chunk_id:
                        document.chunks.remove(chunk)
                        
                        index = self._indexes.get(library_id)
                        if index:
                            index.remove(str(chunk_id))
                        
                        self._persist()
                        return True
            
            return False
    
    def search_library(self, library_id: UUID, query_vector: np.ndarray, k: int) -> List[tuple]:
        """
        Search for k nearest neighbors in a library.
        
        Thread-safe read operation.
        
        Returns:
            List of (chunk_id, distance) tuples
        """
        with self._lock.read_lock():
            index = self._indexes.get(library_id)
            if not index:
                return []
            
            return index.search(query_vector, k)
    
    def _create_index_for_library(self, library: Library) -> None:
        """Create an index for a library based on its index type."""
        if library.index_type == "flat":
            self._indexes[library.id] = FlatIndex()
        elif library.index_type == "ivf":
            self._indexes[library.id] = IVFIndex(n_clusters=100, n_probe=10)
        else:
            # Default to flat
            self._indexes[library.id] = FlatIndex()
    
    def _reindex_library(self, library: Library) -> None:
        """Rebuild the index for a library with all its chunks."""
        index = self._indexes.get(library.id)
        if not index:
            return
        
        index.clear()
        
        vectors = []
        ids = []
        for document in library.documents:
            for chunk in document.chunks:
                vectors.append(chunk.embedding)
                ids.append(str(chunk.id))
        
        if vectors:
            index.add(np.array(vectors), ids)
    
    def _persist(self) -> None:
        """Persist database state to disk."""
        if not self._persistence_path:
            return
        
        try:
            path = Path(self._persistence_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use atomic write pattern
            temp_path = path.with_suffix('.tmp')
            
            with open(temp_path, 'wb') as f:
                pickle.dump({
                    'libraries': self._libraries,
                    'indexes': self._indexes
                }, f)
            
            # Atomic rename
            temp_path.replace(path)
            
        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error persisting database: {e}")
    
    def _load_from_disk(self) -> None:
        """Load database state from disk."""
        if not self._persistence_path:
            return
        
        try:
            path = Path(self._persistence_path)
            if not path.exists():
                return
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self._libraries = data.get('libraries', {})
                self._indexes = data.get('indexes', {})
                
        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error loading database: {e}")
