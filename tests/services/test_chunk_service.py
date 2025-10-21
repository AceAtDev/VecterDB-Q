"""Unit tests for ChunkService."""
import pytest
from unittest.mock import Mock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime

from app.services.chunk_service import ChunkService
from app.domain.models import (
    Chunk, ChunkCreate, ChunkUpdate, ChunkMetadata,
    Library, LibraryMetadata
)


@pytest.fixture
def mock_chunk_repository():
    """Create a mock chunk repository."""
    return Mock()


@pytest.fixture
def mock_library_service():
    """Create a mock library service."""
    return Mock()


@pytest.fixture
def mock_index_repository():
    """Create a mock index repository."""
    return Mock()


@pytest.fixture
def chunk_service(mock_chunk_repository, mock_library_service, mock_index_repository):
    """Create a chunk service with mocked dependencies."""
    return ChunkService(
        repository=mock_chunk_repository,
        library_service=mock_library_service,
        index_repository=mock_index_repository
    )


@pytest.fixture
def sample_library():
    """Create a sample library for testing."""
    return Library(
        id=uuid4(),
        name="Test Library",
        description="A test library",
        metadata=LibraryMetadata(),
        index_type="flat",
        documents=[]
    )


@pytest.fixture
def sample_chunk():
    """Create a sample chunk for testing."""
    return Chunk(
        id=uuid4(),
        text="Test chunk text",
        embedding=[0.1, 0.2, 0.3, 0.4],
        metadata=ChunkMetadata(source="test"),
        document_id=uuid4()
    )


class TestChunkServiceCreate:
    """Tests for chunk creation."""
    
    def test_create_chunk_success(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_library_service,
        mock_index_repository,
        sample_library
    ):
        """Test successfully creating a chunk."""
        # Arrange
        library_id = sample_library.id
        chunk_create = ChunkCreate(
            text="New chunk text",
            embedding=[0.1, 0.2, 0.3],
            metadata=ChunkMetadata(source="test"),
            document_id=uuid4()
        )
        
        created_chunk = Chunk(
            id=uuid4(),
            text=chunk_create.text,
            embedding=chunk_create.embedding,
            metadata=chunk_create.metadata,
            document_id=chunk_create.document_id
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.create_chunk_in_library.return_value = created_chunk
        
        # Act
        result = chunk_service.create_chunk(library_id, chunk_create)
        
        # Assert
        assert result is not None
        assert result.text == chunk_create.text
        assert result.embedding == chunk_create.embedding
        mock_library_service.get_library.assert_called_once_with(library_id)
        mock_chunk_repository.create_chunk_in_library.assert_called_once()
        mock_index_repository.add_vector.assert_called_once_with(
            library_id,
            str(created_chunk.id),
            created_chunk.embedding
        )
    
    def test_create_chunk_library_not_found(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_library_service,
        mock_index_repository
    ):
        """Test creating a chunk when library doesn't exist."""
        # Arrange
        library_id = uuid4()
        chunk_create = ChunkCreate(
            text="New chunk text",
            embedding=[0.1, 0.2, 0.3],
            metadata=ChunkMetadata(source="test")
        )
        
        mock_library_service.get_library.return_value = None
        
        # Act
        result = chunk_service.create_chunk(library_id, chunk_create)
        
        # Assert
        assert result is None
        mock_library_service.get_library.assert_called_once_with(library_id)
        mock_chunk_repository.create_chunk_in_library.assert_not_called()
        mock_index_repository.add_vector.assert_not_called()
    
    def test_create_chunk_adds_to_index(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_library_service,
        mock_index_repository,
        sample_library
    ):
        """Test that creating a chunk adds it to the index."""
        # Arrange
        library_id = sample_library.id
        chunk_create = ChunkCreate(
            text="Test text",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata=ChunkMetadata(source="test")
        )
        
        created_chunk = Chunk(
            id=uuid4(),
            text=chunk_create.text,
            embedding=chunk_create.embedding,
            metadata=chunk_create.metadata
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.create_chunk_in_library.return_value = created_chunk
        
        # Act
        chunk_service.create_chunk(library_id, chunk_create)
        
        # Assert
        mock_index_repository.add_vector.assert_called_once_with(
            library_id,
            str(created_chunk.id),
            created_chunk.embedding
        )


class TestChunkServiceGet:
    """Tests for getting chunks."""
    
    def test_get_chunk_success(
        self,
        chunk_service,
        mock_chunk_repository,
        sample_chunk
    ):
        """Test successfully retrieving a chunk."""
        # Arrange
        library_id = uuid4()
        chunk_id = sample_chunk.id
        mock_chunk_repository.get_chunk.return_value = sample_chunk
        
        # Act
        result = chunk_service.get_chunk(library_id, chunk_id)
        
        # Assert
        assert result is not None
        assert result.id == chunk_id
        assert result.text == sample_chunk.text
        mock_chunk_repository.get_chunk.assert_called_once_with(library_id, chunk_id)
    
    def test_get_chunk_not_found(
        self,
        chunk_service,
        mock_chunk_repository
    ):
        """Test retrieving a non-existent chunk."""
        # Arrange
        library_id = uuid4()
        chunk_id = uuid4()
        mock_chunk_repository.get_chunk.return_value = None
        
        # Act
        result = chunk_service.get_chunk(library_id, chunk_id)
        
        # Assert
        assert result is None
        mock_chunk_repository.get_chunk.assert_called_once_with(library_id, chunk_id)


class TestChunkServiceList:
    """Tests for listing chunks."""
    
    def test_list_chunks_empty(
        self,
        chunk_service,
        mock_chunk_repository
    ):
        """Test listing chunks when none exist."""
        # Arrange
        library_id = uuid4()
        mock_chunk_repository.list_chunks.return_value = []
        
        # Act
        result = chunk_service.list_chunks(library_id)
        
        # Assert
        assert result == []
        mock_chunk_repository.list_chunks.assert_called_once_with(library_id)
    
    def test_list_chunks_multiple(
        self,
        chunk_service,
        mock_chunk_repository
    ):
        """Test listing multiple chunks."""
        # Arrange
        library_id = uuid4()
        chunks = [
            Chunk(id=uuid4(), text="Chunk 1", embedding=[0.1]),
            Chunk(id=uuid4(), text="Chunk 2", embedding=[0.2]),
            Chunk(id=uuid4(), text="Chunk 3", embedding=[0.3])
        ]
        mock_chunk_repository.list_chunks.return_value = chunks
        
        # Act
        result = chunk_service.list_chunks(library_id)
        
        # Assert
        assert len(result) == 3
        assert all(isinstance(chunk, Chunk) for chunk in result)
        mock_chunk_repository.list_chunks.assert_called_once_with(library_id)


class TestChunkServiceUpdate:
    """Tests for updating chunks."""
    
    def test_update_chunk_success(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_chunk
    ):
        """Test successfully updating a chunk."""
        # Arrange
        library_id = uuid4()
        chunk_id = sample_chunk.id
        update_data = ChunkUpdate(
            text="Updated text",
            metadata=ChunkMetadata(source="updated")
        )
        
        mock_chunk_repository.get_chunk.return_value = sample_chunk
        updated_chunk = Chunk(
            id=chunk_id,
            text=update_data.text,
            embedding=sample_chunk.embedding,
            metadata=update_data.metadata
        )
        mock_chunk_repository.update_chunk.return_value = updated_chunk
        
        # Act
        result = chunk_service.update_chunk(library_id, chunk_id, update_data)
        
        # Assert
        assert result is not None
        assert result.text == update_data.text
        mock_chunk_repository.get_chunk.assert_called_once_with(library_id, chunk_id)
        mock_chunk_repository.update_chunk.assert_called_once()
    
    def test_update_chunk_not_found(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_index_repository
    ):
        """Test updating a non-existent chunk."""
        # Arrange
        library_id = uuid4()
        chunk_id = uuid4()
        update_data = ChunkUpdate(text="Updated text")
        mock_chunk_repository.get_chunk.return_value = None
        
        # Act
        result = chunk_service.update_chunk(library_id, chunk_id, update_data)
        
        # Assert
        assert result is None
        mock_chunk_repository.get_chunk.assert_called_once_with(library_id, chunk_id)
        mock_chunk_repository.update_chunk.assert_not_called()
    
    def test_update_chunk_embedding_updates_index(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_chunk
    ):
        """Test that updating chunk embedding updates the index."""
        # Arrange
        library_id = uuid4()
        chunk_id = sample_chunk.id
        new_embedding = [0.9, 0.8, 0.7, 0.6]
        update_data = ChunkUpdate(embedding=new_embedding)
        
        mock_chunk_repository.get_chunk.return_value = sample_chunk
        updated_chunk = Chunk(
            id=chunk_id,
            text=sample_chunk.text,
            embedding=new_embedding,
            metadata=sample_chunk.metadata
        )
        mock_chunk_repository.update_chunk.return_value = updated_chunk
        
        # Act
        chunk_service.update_chunk(library_id, chunk_id, update_data)
        
        # Assert
        mock_index_repository.update_vector.assert_called_once_with(
            library_id,
            str(chunk_id),
            new_embedding
        )


class TestChunkServiceDelete:
    """Tests for deleting chunks."""
    
    def test_delete_chunk_success(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_index_repository
    ):
        """Test successfully deleting a chunk."""
        # Arrange
        library_id = uuid4()
        chunk_id = uuid4()
        mock_chunk_repository.delete_chunk.return_value = True
        
        # Act
        result = chunk_service.delete_chunk(library_id, chunk_id)
        
        # Assert
        assert result is True
        mock_chunk_repository.delete_chunk.assert_called_once_with(library_id, chunk_id)
        mock_index_repository.remove_vector.assert_called_once_with(library_id, str(chunk_id))
    
    def test_delete_chunk_not_found(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_index_repository
    ):
        """Test deleting a non-existent chunk."""
        # Arrange
        library_id = uuid4()
        chunk_id = uuid4()
        mock_chunk_repository.delete_chunk.return_value = False
        
        # Act
        result = chunk_service.delete_chunk(library_id, chunk_id)
        
        # Assert
        assert result is False
        mock_chunk_repository.delete_chunk.assert_called_once_with(library_id, chunk_id)
        mock_index_repository.remove_vector.assert_not_called()
    
    def test_delete_chunk_updates_index(
        self,
        chunk_service,
        mock_chunk_repository,
        mock_index_repository
    ):
        """Test that deleting a chunk removes it from the index."""
        # Arrange
        library_id = uuid4()
        chunk_id = uuid4()
        mock_chunk_repository.delete_chunk.return_value = True
        
        # Act
        chunk_service.delete_chunk(library_id, chunk_id)
        
        # Assert
        mock_index_repository.remove_vector.assert_called_once_with(
            library_id,
            str(chunk_id)
        )
