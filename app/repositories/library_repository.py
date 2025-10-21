"""Library repository for managing library entities with persistence."""
from typing import Dict, Optional, List
from uuid import UUID
import pickle
from pathlib import Path

from app.domain.models import Library
from app.repositories.base_repository import BaseRepository


class LibraryRepository(BaseRepository[Library]):
    """Repository for library management with thread-safe access and persistence.
    
    Responsibilities:
    - Store and retrieve library entities
    - Ensure thread-safe concurrent access
    - Persist library data to disk
    - Single Responsibility: Library data access only
    """
    
    def __init__(self, persistence_path: Optional[str] = None) -> None:
        """Initialize library repository.
        
        Args:
            persistence_path: Optional path to persist library data
        """
        super().__init__()
        self._libraries: Dict[UUID, Library] = {}
        self._persistence_path = persistence_path
        
        print(f"[LIBRARY_REPO] 🚀 Initialized LibraryRepository")
        print(f"[LIBRARY_REPO] Persistence path: {persistence_path}")
        
        if self._persistence_path:
            self._load_from_disk()
        else:
            print(f"[LIBRARY_REPO] ⚠️ Persistence disabled")
    
    def save(self, entity: Library) -> Library:
        """Save a library entity.
        
        Args:
            entity: Library to save
            
        Returns:
            Saved library
            
        Raises:
            ValueError: If library with same ID already exists
        """
        with self._lock.write_lock():
            if entity.id in self._libraries:
                raise ValueError(f"Library with ID {entity.id} already exists")
            
            self._libraries[entity.id] = entity
            self._persist()
            print(f"[LIBRARY_REPO] ✅ Saved library: {entity.name} (ID: {entity.id})")
            return entity
    
    def find_by_id(self, id: UUID) -> Optional[Library]:
        """Find a library by ID.
        
        Args:
            id: UUID of the library
            
        Returns:
            Library if found, None otherwise
        """
        with self._lock.read_lock():
            return self._libraries.get(id)
    
    def find_all(self) -> List[Library]:
        """Retrieve all libraries.
        
        Returns:
            List of all libraries
        """
        with self._lock.read_lock():
            return list(self._libraries.values())
    
    def delete(self, id: UUID) -> bool:
        """Delete a library by ID.
        
        Args:
            id: UUID of the library to delete
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock.write_lock():
            if id not in self._libraries:
                return False
            
            del self._libraries[id]
            self._persist()
            print(f"[LIBRARY_REPO] 🗑️ Deleted library: {id}")
            return True
    
    # Legacy methods for backward compatibility with existing service layer
    def create_library(self, library: Library) -> Library:
        """Create a new library (legacy method)."""
        return self.save(library)
    
    def get_library(self, library_id: UUID) -> Optional[Library]:
        """Get library by ID (legacy method)."""
        return self.find_by_id(library_id)
    
    def list_libraries(self) -> List[Library]:
        """List all libraries (legacy method)."""
        return self.find_all()
    
    def update_library(self, library_id: UUID, library: Library) -> Optional[Library]:
        """Update an existing library.
        
        Args:
            library_id: UUID of library to update
            library: Updated library object
            
        Returns:
            Updated library if found, None otherwise
        """
        with self._lock.write_lock():
            if library_id not in self._libraries:
                return None
            
            self._libraries[library_id] = library
            self._persist()
            print(f"[LIBRARY_REPO] 📝 Updated library: {library.name} (ID: {library_id})")
            return library
    
    def delete_library(self, library_id: UUID) -> bool:
        """Delete a library (legacy method)."""
        return self.delete(library_id)
    
    def _persist(self) -> None:
        """Persist library data to disk."""
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
            
            # Save to libraries.pkl inside the directory
            path = base_path / "libraries.pkl"
            
            # Atomic write pattern
            temp_path = path.with_suffix('.tmp')
            
            with open(temp_path, 'wb') as f:
                pickle.dump(self._libraries, f)
            
            # Atomic rename
            temp_path.replace(path)
            
        except Exception as e:
            print(f"[LIBRARY_REPO] ❌ Error persisting libraries: {e}")
    
    def _load_from_disk(self) -> None:
        """Load library data from disk."""
        if not self._persistence_path:
            return
        
        try:
            # Ensure persistence_path is treated as a directory
            base_path = Path(self._persistence_path)
            if base_path.suffix == '.pkl':
                # Remove .pkl extension if present (legacy compatibility)
                base_path = base_path.with_suffix('')
            
            path = base_path / "libraries.pkl"
            if not path.exists():
                print(f"[LIBRARY_REPO] No persistence file found at {path}")
                return
            
            print(f"[LIBRARY_REPO] 📂 Loading libraries from {path}")
            with open(path, 'rb') as f:
                self._libraries = pickle.load(f)
            
            print(f"[LIBRARY_REPO] ✅ Loaded {len(self._libraries)} libraries")
            
        except Exception as e:
            print(f"[LIBRARY_REPO] ❌ Error loading libraries: {e}")
            import traceback
            traceback.print_exc()
