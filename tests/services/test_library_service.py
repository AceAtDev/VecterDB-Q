"""Unit tests for LibraryService."""
import pytest
from unittest.mock import Mock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime

from app.services.library_service import LibraryService
from app.domain.models import Library, LibraryCreate, LibraryUpdate, LibraryMetadata


@pytest.fixture
def mock_library_repository():
    """Create a mock library repository."""
    return Mock()


@pytest.fixture
def mock_index_repository():
    """Create a mock index repository."""
    return Mock()


@pytest.fixture
def mock_chunk_repository():
    """Create a mock chunk repository."""
    mock_repo = Mock()
    mock_repo.get_documents_for_library.return_value = []
    return mock_repo


@pytest.fixture
def library_service(mock_library_repository, mock_index_repository, mock_chunk_repository):
    """Create a library service with mocked dependencies."""
    return LibraryService(
        repository=mock_library_repository,
        index_repository=mock_index_repository,
        chunk_repository=mock_chunk_repository
    )


@pytest.fixture
def sample_library():
    """Create a sample library for testing."""
    return Library(
        id=uuid4(),
        name="Test Library",
        description="A test library",
        metadata=LibraryMetadata(category="test", tags=["testing"]),
        index_type="flat",
        documents=[]
    )


class TestLibraryServiceCreate:
    """Tests for library creation."""
    
    def test_create_library_success(self, library_service, mock_library_repository, mock_index_repository):
        """Test successful library creation."""
        # Arrange
        library_create = LibraryCreate(
            name="New Library",
            description="A new library",
            metadata=LibraryMetadata(category="test"),
            index_type="flat"
        )
        
        expected_library = Library(
            id=uuid4(),
            name=library_create.name,
            description=library_create.description,
            metadata=library_create.metadata,
            index_type=library_create.index_type,
            documents=[]
        )
        
        mock_library_repository.create_library.return_value = expected_library
        
        # Act
        result = library_service.create_library(library_create)
        
        # Assert
        assert result.name == library_create.name
        assert result.description == library_create.description
        assert result.index_type == library_create.index_type
        mock_library_repository.create_library.assert_called_once()
        mock_index_repository.create_index.assert_called_once_with(
            expected_library.id, 
            expected_library.index_type
        )
    
    def test_create_library_without_index_repository(self, mock_library_repository, mock_chunk_repository):
        """Test library creation when index repository is not provided."""
        # Arrange
        service = LibraryService(
            repository=mock_library_repository,
            index_repository=None,
            chunk_repository=mock_chunk_repository
        )
        
        library_create = LibraryCreate(
            name="New Library",
            description="Test",
            metadata=LibraryMetadata(),
            index_type="flat"
        )
        
        expected_library = Library(
            id=uuid4(),
            name=library_create.name,
            description=library_create.description,
            metadata=library_create.metadata,
            index_type=library_create.index_type,
            documents=[]
        )
        
        mock_library_repository.create_library.return_value = expected_library
        
        # Act
        result = service.create_library(library_create)
        
        # Assert
        assert result.name == library_create.name
        mock_library_repository.create_library.assert_called_once()


class TestLibraryServiceGet:
    """Tests for getting libraries."""
    
    def test_get_library_success(self, library_service, mock_library_repository, sample_library):
        """Test successfully retrieving a library."""
        # Arrange
        library_id = sample_library.id
        mock_library_repository.get_library.return_value = sample_library
        
        # Act
        result = library_service.get_library(library_id)
        
        # Assert
        assert result is not None
        assert result.id == library_id
        assert result.name == sample_library.name
        mock_library_repository.get_library.assert_called_once_with(library_id)
    
    def test_get_library_not_found(self, library_service, mock_library_repository):
        """Test retrieving a non-existent library."""
        # Arrange
        library_id = uuid4()
        mock_library_repository.get_library.return_value = None
        
        # Act
        result = library_service.get_library(library_id)
        
        # Assert
        assert result is None
        mock_library_repository.get_library.assert_called_once_with(library_id)
    
    def test_get_library_hydrates_documents(
        self, 
        library_service, 
        mock_library_repository,
        mock_chunk_repository,
        sample_library
    ):
        """Test that get_library hydrates library with documents."""
        # Arrange
        library_id = sample_library.id
        mock_library_repository.get_library.return_value = sample_library
        mock_documents = [Mock(id=uuid4()), Mock(id=uuid4())]
        mock_chunk_repository.get_documents_for_library.return_value = mock_documents
        
        # Act
        result = library_service.get_library(library_id)
        
        # Assert
        assert result.documents == mock_documents
        mock_chunk_repository.get_documents_for_library.assert_called_once_with(library_id)


class TestLibraryServiceList:
    """Tests for listing libraries."""
    
    def test_list_libraries_empty(self, library_service, mock_library_repository):
        """Test listing libraries when none exist."""
        # Arrange
        mock_library_repository.list_libraries.return_value = []
        
        # Act
        result = library_service.list_libraries()
        
        # Assert
        assert result == []
        mock_library_repository.list_libraries.assert_called_once()
    
    def test_list_libraries_multiple(self, library_service, mock_library_repository):
        """Test listing multiple libraries."""
        # Arrange
        libraries = [
            Library(id=uuid4(), name="Library 1", documents=[]),
            Library(id=uuid4(), name="Library 2", documents=[]),
            Library(id=uuid4(), name="Library 3", documents=[])
        ]
        mock_library_repository.list_libraries.return_value = libraries
        
        # Act
        result = library_service.list_libraries()
        
        # Assert
        assert len(result) == 3
        assert all(isinstance(lib, Library) for lib in result)
        mock_library_repository.list_libraries.assert_called_once()
    
    def test_list_libraries_hydrates_all(
        self,
        library_service,
        mock_library_repository,
        mock_chunk_repository
    ):
        """Test that list_libraries hydrates all libraries with documents."""
        # Arrange
        lib1 = Library(id=uuid4(), name="Library 1", documents=[])
        lib2 = Library(id=uuid4(), name="Library 2", documents=[])
        mock_library_repository.list_libraries.return_value = [lib1, lib2]
        
        mock_docs_1 = [Mock(id=uuid4())]
        mock_docs_2 = [Mock(id=uuid4()), Mock(id=uuid4())]
        mock_chunk_repository.get_documents_for_library.side_effect = [mock_docs_1, mock_docs_2]
        
        # Act
        result = library_service.list_libraries()
        
        # Assert
        assert len(result) == 2
        assert result[0].documents == mock_docs_1
        assert result[1].documents == mock_docs_2
        assert mock_chunk_repository.get_documents_for_library.call_count == 2


class TestLibraryServiceUpdate:
    """Tests for updating libraries."""
    
    def test_update_library_success(
        self,
        library_service,
        mock_library_repository,
        sample_library
    ):
        """Test successfully updating a library."""
        # Arrange
        library_id = sample_library.id
        update_data = LibraryUpdate(
            name="Updated Name",
            description="Updated description"
        )
        
        mock_library_repository.get_library.return_value = sample_library
        updated_library = Library(
            id=library_id,
            name=update_data.name,
            description=update_data.description,
            metadata=sample_library.metadata,
            index_type=sample_library.index_type,
            documents=[]
        )
        mock_library_repository.update_library.return_value = updated_library
        
        # Act
        result = library_service.update_library(library_id, update_data)
        
        # Assert
        assert result is not None
        assert result.name == update_data.name
        assert result.description == update_data.description
        mock_library_repository.get_library.assert_called_once_with(library_id)
        mock_library_repository.update_library.assert_called_once()
    
    def test_update_library_not_found(self, library_service, mock_library_repository):
        """Test updating a non-existent library."""
        # Arrange
        library_id = uuid4()
        update_data = LibraryUpdate(name="Updated Name")
        mock_library_repository.get_library.return_value = None
        
        # Act
        result = library_service.update_library(library_id, update_data)
        
        # Assert
        assert result is None
        mock_library_repository.get_library.assert_called_once_with(library_id)
        mock_library_repository.update_library.assert_not_called()
    
    def test_update_library_index_type_recreates_index(
        self,
        library_service,
        mock_library_repository,
        mock_index_repository,
        sample_library
    ):
        """Test that changing index type recreates the index."""
        # Arrange
        library_id = sample_library.id
        sample_library.index_type = "flat"
        update_data = LibraryUpdate(index_type="ivf")
        
        mock_library_repository.get_library.return_value = sample_library
        updated_library = Library(
            id=library_id,
            name=sample_library.name,
            description=sample_library.description,
            metadata=sample_library.metadata,
            index_type="ivf",
            documents=[]
        )
        mock_library_repository.update_library.return_value = updated_library
        
        # Act
        result = library_service.update_library(library_id, update_data)
        
        # Assert
        assert result.index_type == "ivf"
        mock_index_repository.delete_index.assert_called_once_with(library_id)
        mock_index_repository.create_index.assert_called_once_with(library_id, "ivf")


class TestLibraryServiceDelete:
    """Tests for deleting libraries."""
    
    def test_delete_library_success(
        self,
        library_service,
        mock_library_repository,
        mock_index_repository
    ):
        """Test successfully deleting a library."""
        # Arrange
        library_id = uuid4()
        mock_library_repository.delete_library.return_value = True
        
        # Act
        result = library_service.delete_library(library_id)
        
        # Assert
        assert result is True
        mock_library_repository.delete_library.assert_called_once_with(library_id)
        mock_index_repository.delete_index.assert_called_once_with(library_id)
    
    def test_delete_library_not_found(
        self,
        library_service,
        mock_library_repository,
        mock_index_repository
    ):
        """Test deleting a non-existent library."""
        # Arrange
        library_id = uuid4()
        mock_library_repository.delete_library.return_value = False
        
        # Act
        result = library_service.delete_library(library_id)
        
        # Assert
        assert result is False
        mock_library_repository.delete_library.assert_called_once_with(library_id)
        mock_index_repository.delete_index.assert_not_called()
