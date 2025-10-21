"""Unit tests for SearchService."""
import pytest
from unittest.mock import Mock, MagicMock
from uuid import UUID, uuid4
import numpy as np

from app.services.search_service import SearchService
from app.domain.models import (
    SearchQuery, SearchResult, Chunk, ChunkMetadata,
    Library, LibraryMetadata, Document
)


@pytest.fixture
def mock_library_service():
    """Create a mock library service."""
    return Mock()


@pytest.fixture
def mock_chunk_repository():
    """Create a mock chunk repository."""
    return Mock()


@pytest.fixture
def mock_index_repository():
    """Create a mock index repository."""
    return Mock()


@pytest.fixture
def search_service(mock_library_service, mock_chunk_repository, mock_index_repository):
    """Create a search service with mocked dependencies."""
    return SearchService(
        library_service=mock_library_service,
        chunk_repository=mock_chunk_repository,
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
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        Chunk(
            id=uuid4(),
            text="First chunk about science",
            embedding=[0.1, 0.2, 0.3, 0.4],
            metadata=ChunkMetadata(
                source="doc1",
                author="John Doe",
                custom={"category": "science"}
            )
        ),
        Chunk(
            id=uuid4(),
            text="Second chunk about technology",
            embedding=[0.2, 0.3, 0.4, 0.5],
            metadata=ChunkMetadata(
                source="doc2",
                author="Jane Smith",
                custom={"category": "technology"}
            )
        ),
        Chunk(
            id=uuid4(),
            text="Third chunk about science",
            embedding=[0.3, 0.4, 0.5, 0.6],
            metadata=ChunkMetadata(
                source="doc3",
                author="Bob Johnson",
                custom={"category": "science"}
            )
        )
    ]


@pytest.fixture
def sample_documents(sample_chunks):
    """Create sample documents with chunks."""
    from app.domain.models import DocumentMetadata
    
    return [
        Document(
            id=uuid4(),
            chunks=[sample_chunks[0]],
            metadata=DocumentMetadata(title="doc1.txt")
        ),
        Document(
            id=uuid4(),
            chunks=[sample_chunks[1], sample_chunks[2]],
            metadata=DocumentMetadata(title="doc2.txt")
        )
    ]


class TestSearchServiceBasic:
    """Tests for basic search functionality."""
    
    def test_search_returns_results(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test that search returns results successfully."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=2,
            metric="cosine"
        )
        
        # Mock library exists
        mock_library_service.get_library.return_value = sample_library
        
        # Mock documents in library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        # Mock index search results (chunk_id, distance)
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[0].id), 0.1),
            (str(sample_chunks[1].id), 0.2)
        ]
        
        # Mock chunk retrieval
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].chunk.id == sample_chunks[0].id
        assert results[1].chunk.id == sample_chunks[1].id
        # Verify scores are calculated (cosine: score = 1 - distance)
        assert results[0].score == pytest.approx(0.9, rel=0.01)  # 1 - 0.1
        assert results[1].score == pytest.approx(0.8, rel=0.01)  # 1 - 0.2
        
        # Verify dependencies were called
        mock_library_service.get_library.assert_called_once_with(library_id)
        mock_index_repository.search_library.assert_called_once()
    
    def test_search_library_not_found(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository
    ):
        """Test search when library doesn't exist."""
        # Arrange
        library_id = uuid4()
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3],
            k=5,
            metric="cosine"
        )
        
        mock_library_service.get_library.return_value = None
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert
        assert results == []
        mock_library_service.get_library.assert_called_once_with(library_id)
        mock_chunk_repository.get_documents_for_library.assert_not_called()
        mock_index_repository.search_library.assert_not_called()
    
    def test_search_empty_index(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library
    ):
        """Test search when index returns no results."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3],
            k=5,
            metric="cosine"
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = []
        mock_index_repository.search_library.return_value = []
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert
        assert results == []
        mock_index_repository.search_library.assert_called_once()


class TestSearchServiceFiltering:
    """Tests for metadata filtering functionality."""
    
    def test_search_with_filters_matches(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test search with metadata filters that match chunks."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=5,
            metric="cosine",
            filters={"custom.category": "science"}  # Should match chunks 0 and 2
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        # Return all chunks from index
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[0].id), 0.1),
            (str(sample_chunks[1].id), 0.15),
            (str(sample_chunks[2].id), 0.2)
        ]
        
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert - only science chunks should be returned
        assert len(results) == 2
        assert results[0].chunk.metadata.custom["category"] == "science"
        assert results[1].chunk.metadata.custom["category"] == "science"
        assert results[0].chunk.id == sample_chunks[0].id
        assert results[1].chunk.id == sample_chunks[2].id
    
    def test_search_with_filters_no_matches(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test search with filters that match no chunks."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=5,
            metric="cosine",
            filters={"custom.category": "history"}  # No chunks with this category
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[0].id), 0.1),
            (str(sample_chunks[1].id), 0.2)
        ]
        
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert
        assert results == []
    
    def test_search_with_multiple_filters(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test search with multiple metadata filters."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=5,
            metric="cosine",
            filters={
                "custom.category": "science",
                "author": "John Doe"
            }
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[0].id), 0.1),
            (str(sample_chunks[2].id), 0.2)
        ]
        
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert - only chunk 0 matches both filters
        assert len(results) == 1
        assert results[0].chunk.id == sample_chunks[0].id
        assert results[0].chunk.metadata.custom["category"] == "science"
        assert results[0].chunk.metadata.author == "John Doe"


class TestSearchServiceMetrics:
    """Tests for different distance metrics."""
    
    def test_search_with_euclidean_metric(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test search with Euclidean distance metric."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=2,
            metric="euclidean"
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        # Mock index returns euclidean distances
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[0].id), 0.5),  # distance = 0.5
            (str(sample_chunks[1].id), 1.0)   # distance = 1.0
        ]
        
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert
        assert len(results) == 2
        # Euclidean score = 1 / (1 + distance)
        assert results[0].score == pytest.approx(1.0 / 1.5, rel=0.01)  # 1/(1+0.5)
        assert results[1].score == pytest.approx(1.0 / 2.0, rel=0.01)  # 1/(1+1.0)
        assert results[0].distance == 0.5
        assert results[1].distance == 1.0
    
    def test_search_results_sorted_by_score(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test that search results are sorted by score (descending)."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=3,
            metric="cosine"
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        # Return results in non-sorted order
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[1].id), 0.3),  # score = 0.7
            (str(sample_chunks[0].id), 0.1),  # score = 0.9 (best)
            (str(sample_chunks[2].id), 0.2)   # score = 0.8
        ]
        
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert - results should be sorted by score
        assert len(results) == 3
        assert results[0].chunk.id == sample_chunks[0].id  # Best score
        assert results[1].chunk.id == sample_chunks[2].id  # Second
        assert results[2].chunk.id == sample_chunks[1].id  # Third
        assert results[0].score > results[1].score > results[2].score


class TestSearchServiceEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_search_chunk_not_found_in_repository(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test search when index returns chunk ID that doesn't exist in repository."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=3,
            metric="cosine"
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        # Index returns valid and invalid chunk IDs
        phantom_chunk_id = uuid4()
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[0].id), 0.1),
            (str(phantom_chunk_id), 0.15),  # This chunk doesn't exist
            (str(sample_chunks[1].id), 0.2)
        ]
        
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None  # Phantom chunk not found
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert - should skip phantom chunk and return only valid ones
        assert len(results) == 2
        assert results[0].chunk.id == sample_chunks[0].id
        assert results[1].chunk.id == sample_chunks[1].id
    
    def test_search_respects_k_limit(
        self,
        search_service,
        mock_library_service,
        mock_chunk_repository,
        mock_index_repository,
        sample_library,
        sample_chunks,
        sample_documents
    ):
        """Test that search returns at most k results."""
        # Arrange
        library_id = sample_library.id
        search_query = SearchQuery(
            embedding=[0.1, 0.2, 0.3, 0.4],
            k=1,  # Request only 1 result
            metric="cosine"
        )
        
        mock_library_service.get_library.return_value = sample_library
        mock_chunk_repository.get_documents_for_library.return_value = sample_documents
        
        # Index returns multiple results
        mock_index_repository.search_library.return_value = [
            (str(sample_chunks[0].id), 0.1),
            (str(sample_chunks[1].id), 0.2),
            (str(sample_chunks[2].id), 0.3)
        ]
        
        def get_chunk_side_effect(lib_id, chunk_id):
            for chunk in sample_chunks:
                if chunk.id == chunk_id:
                    return chunk
            return None
        
        mock_chunk_repository.get_chunk.side_effect = get_chunk_side_effect
        
        # Act
        results = search_service.search(library_id, search_query)
        
        # Assert - should return only 1 result (best score)
        assert len(results) == 1
        assert results[0].chunk.id == sample_chunks[0].id


class TestMatchesFilters:
    """Tests for the _matches_filters static method."""
    
    def test_matches_filters_simple_match(self, search_service):
        """Test filter matching with simple string match."""
        # Arrange
        chunk = Chunk(
            id=uuid4(),
            text="Test",
            embedding=[0.1],
            metadata=ChunkMetadata(
                source="test.txt",
                custom={"category": "science"}
            )
        )
        filters = {"custom.category": "science"}
        
        # Act
        result = search_service._matches_filters(chunk, filters)
        
        # Assert
        assert result is True
    
    def test_matches_filters_case_insensitive(self, search_service):
        """Test filter matching is case-insensitive."""
        # Arrange
        chunk = Chunk(
            id=uuid4(),
            text="Test",
            embedding=[0.1],
            metadata=ChunkMetadata(
                source="test.txt",
                custom={"category": "Science"}
            )
        )
        filters = {"custom.category": "science"}
        
        # Act
        result = search_service._matches_filters(chunk, filters)
        
        # Assert
        assert result is True
    
    def test_matches_filters_substring_match(self, search_service):
        """Test filter matching with substring."""
        # Arrange
        chunk = Chunk(
            id=uuid4(),
            text="Test",
            embedding=[0.1],
            metadata=ChunkMetadata(
                source="test.txt",
                author="John Doe Smith"
            )
        )
        filters = {"author": "Doe"}
        
        # Act
        result = search_service._matches_filters(chunk, filters)
        
        # Assert
        assert result is True
    
    def test_matches_filters_no_match(self, search_service):
        """Test filter matching when metadata doesn't match."""
        # Arrange
        chunk = Chunk(
            id=uuid4(),
            text="Test",
            embedding=[0.1],
            metadata=ChunkMetadata(
                source="test.txt",
                custom={"category": "science"}
            )
        )
        filters = {"custom.category": "history"}
        
        # Act
        result = search_service._matches_filters(chunk, filters)
        
        # Assert
        assert result is False
    
    def test_matches_filters_missing_key(self, search_service):
        """Test filter matching when metadata key doesn't exist."""
        # Arrange
        chunk = Chunk(
            id=uuid4(),
            text="Test",
            embedding=[0.1],
            metadata=ChunkMetadata(source="test.txt")
        )
        filters = {"nonexistent_key": "value"}
        
        # Act
        result = search_service._matches_filters(chunk, filters)
        
        # Assert
        assert result is False
