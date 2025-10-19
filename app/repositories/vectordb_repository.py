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
        print(f"[REPO] 🚀 Initializing VectorDBRepository")
        self._libraries: Dict[UUID, Library] = {}
        self._indexes: Dict[UUID, VectorIndex] = {}
        self._lock = RWLock()
        self._persistence_path = persistence_path
        
        print(f"[REPO] Persistence path: {persistence_path}")
        if self._persistence_path:
            self._load_from_disk()
        else:
            print(f"[REPO] ⚠️ Persistence disabled")
    
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
        """
        DEPRECATED: Use create_chunk_in_library instead.
        Add a chunk to a library. This method should be called AFTER the chunk is added to the document in the library.
        """
        with self._lock.write_lock():
            library = self._libraries.get(library_id)
            if not library:
                print(f"   [REPO] ❌ Library {library_id} not found when adding chunk")
                return None
            
            # Verify chunk exists in library's documents
            chunk_found = False
            for doc in library.documents:
                for existing_chunk in doc.chunks:
                    if existing_chunk.id == chunk.id:
                        chunk_found = True
                        break
                if chunk_found:
                    break
            
            if not chunk_found:
                print(f"   [REPO] ⚠️ Chunk {chunk.id} not found in library documents! This shouldn't happen.")
            else:
                print(f"   [REPO] ✅ Chunk {chunk.id} found in library documents")
            
            # Add chunk to index
            index = self._indexes.get(library_id)
            print(f"   [REPO] Adding chunk to index: {type(index).__name__ if index is not None else 'None'}")
            if index is not None:
                vector = np.array(chunk.embedding)
                print(f"   [REPO] Vector shape: {vector.shape}, chunk ID: {chunk.id}")
                index.add(np.array([vector]), [str(chunk.id)])
                print(f"   [REPO] ✅ Chunk added to index. Index now has {len(index)} vectors")
            else:
                print(f"   [REPO] ⚠️ No index found for library!")
            
            self._persist()
            return chunk
    
    def create_chunk_in_library(self, library_id: UUID, chunk: Chunk) -> Optional[Chunk]:
        """Create a chunk and add it to a library with proper locking."""
        with self._lock.write_lock():
            library = self._libraries.get(library_id)
            if not library:
                print(f"   [REPO] ❌ Library {library_id} not found when creating chunk")
                return None
            
            from app.domain.models import Document, DocumentMetadata
            from datetime import datetime
            
            # Find or create document for this chunk
            document = None
            if chunk.document_id:
                for doc in library.documents:
                    if doc.id == chunk.document_id:
                        document = doc
                        break
            
            if not document:
                # Create a new default document
                document = Document(
                    library_id=library_id,
                    metadata=DocumentMetadata(title="Default Document")
                )
                library.documents.append(document)
                chunk.document_id = document.id
                print(f"   [REPO] 📄 Created new document {document.id} for library {library_id}")
            
            # Add chunk to document
            document.chunks.append(chunk)
            document.updated_at = datetime.utcnow()
            library.updated_at = datetime.utcnow()
            
            print(f"   [REPO] 📝 Added chunk {chunk.id} to document {document.id}")
            
            # Add chunk to index
            index = self._indexes.get(library_id)
            print(f"   [REPO] Adding chunk to index: {type(index).__name__ if index is not None else 'None'}")
            if index is not None:
                vector = np.array(chunk.embedding)
                print(f"   [REPO] Vector shape: {vector.shape}, chunk ID: {chunk.id}")
                index.add(np.array([vector]), [str(chunk.id)])
                print(f"   [REPO] ✅ Chunk added to index. Index now has {len(index)} vectors")
            else:
                print(f"   [REPO] ⚠️ No index found for library!")
            
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
                        if index is not None:
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
                        if index is not None:
                            index.remove(str(chunk_id))
                        
                        self._persist()
                        return True
            
            return False
    
    def search_library(self, library_id: UUID, query_vector: np.ndarray, k: int, metric: str = "euclidean") -> List[tuple]:
        with self._lock.read_lock():
            index = self._indexes.get(library_id)
            print(f"   [REPO] Index for library {library_id}: {type(index).__name__ if index is not None else 'None'}")
            if index is None:
                print(f"   [REPO] ❌ No index found for library!")
                return []
            
            print(f"   [REPO] Index has {len(index)} vectors")
            results = index.search(query_vector, k, metric)
            print(f"   [REPO] Index returned {len(results)} results")
            return results
    
    def _create_index_for_library(self, library: Library) -> None:
        """Create an index for a library based on its index type."""
        print(f"[REPO] _create_index_for_library called for {library.id}, type: {library.index_type}")
        
        try:
            if library.index_type == "flat":
                self._indexes[library.id] = FlatIndex()
                print(f"[REPO] Created FlatIndex for {library.id}")
            elif library.index_type == "ivf":
                self._indexes[library.id] = IVFIndex(n_clusters=100, n_probe=10)
                print(f"[REPO] Created IVFIndex for {library.id}")
            else:
                # Default to flat
                self._indexes[library.id] = FlatIndex()
                print(f"[REPO] Created FlatIndex (default) for {library.id}")
            
            # Verify it was set
            if library.id in self._indexes:
                index = self._indexes[library.id]
                print(f"[REPO] ✅ Index stored: {type(index).__name__}, {type(index)}")
            else:
                print(f"[REPO] ❌ Index NOT in dict after creation!")
        except Exception as e:
            print(f"[REPO] ❌ Exception creating index: {e}")
            import traceback
            traceback.print_exc()
    
    def _reindex_library(self, library: Library) -> None:
        """Rebuild the index for a library with all its chunks."""
        index = self._indexes.get(library.id)
        if index is None:
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
                print(f"[REPO] No persistence file found at {path}")
                return
            
            print(f"[REPO] 📂 Loading database from {path}")
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self._libraries = data.get('libraries', {})
                # Don't load indexes from disk - they need to be rebuilt
                # self._indexes = data.get('indexes', {})
                
            print(f"[REPO] ✅ Loaded {len(self._libraries)} libraries")
            
            # Recreate indexes for all libraries
            for library in self._libraries.values():
                total_chunks = sum(len(doc.chunks) for doc in library.documents)
                print(f"[REPO] 🔨 Recreating index for library: {library.name} (ID: {library.id})")
                print(f"[REPO]    Library ID type: {type(library.id)}, value: {library.id}")
                print(f"[REPO]    Index type: {library.index_type}, Total chunks: {total_chunks}")
                
                self._create_index_for_library(library)
                
                # Verify index was created
                print(f"[REPO]    Checking if {library.id} is in _indexes...")
                print(f"[REPO]    _indexes keys: {list(self._indexes.keys())}")
                print(f"[REPO]    Trying different access methods...")
                
                # Try direct key access
                try:
                    index_direct = self._indexes[library.id]
                    print(f"[REPO]    Direct access [library.id]: {type(index_direct).__name__}")
                except KeyError as e:
                    print(f"[REPO]    Direct access [library.id] FAILED: {e}")
                
                # Try .get()
                index = self._indexes.get(library.id)
                print(f"[REPO]    .get(library.id): {index}")
                print(f"[REPO]    .get(library.id) type: {type(index)}")
                
                # Check if library.id is in the dict
                in_dict = library.id in self._indexes
                print(f"[REPO]    library.id in self._indexes: {in_dict}")
                
                # Try iterating
                for key, value in self._indexes.items():
                    print(f"[REPO]    Key: {key} ({type(key)}), equals library.id: {key == library.id}, Value: {type(value).__name__}")
                
                if index is not None:  # Use 'is not None' instead of 'if index is not None:'
                    print(f"[REPO]    ✅ Index created: {type(index).__name__}, len={len(index)}")
                    print(f"[REPO]    ✅ Index created: {type(index).__name__}")
                else:
                    print(f"[REPO]    ❌ Index creation failed!")
                    print(f"[REPO]    ❌ library.id={library.id}, type={type(library.id)}")
                    print(f"[REPO]    ❌ Keys in _indexes: {[str(k) for k in self._indexes.keys()]}")
                
                self._reindex_library(library)
                
                # Verify reindexing worked
                index = self._indexes.get(library.id)
                if index is not None:  # Use 'is not None' instead of 'if index is not None:'
                    print(f"[REPO]    ✅ Index rebuilt with {len(index)} vectors")
                else:
                    print(f"[REPO]    ❌ Index is None after reindexing!")
                
        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"[REPO] ❌ Error loading database: {e}")
            import traceback
            traceback.print_exc()

