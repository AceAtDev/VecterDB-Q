"""Demo script to interact with the VectorDB API."""
import httpx
import numpy as np
from typing import List


# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
COHERE_API_KEY = "REDACTED_COHERE_KEY"


def create_embedding(text: str) -> List[float]:
    """
    Create embedding using Cohere API.
    
    For testing purposes, we'll use a simple mock embedding.
    In production, you would call the actual Cohere API.
    """
    # Mock embedding based on text hash for demonstration
    np.random.seed(hash(text) % (2**32))
    return np.random.randn(768).tolist()


def main():
    """Run API demonstration."""
    print("=" * 60)
    print("VectorDB-Q API Demo")
    print("=" * 60)
    
    with httpx.Client() as client:
        # 1. Create a library
        print("\n1. Creating a library...")
        library_data = {
            "name": "Technical Documentation",
            "description": "A collection of technical documents",
            "metadata": {
                "category": "technical",
                "language": "en",
                "tags": ["documentation", "api"]
            },
            "index_type": "flat"
        }
        
        response = client.post(f"{API_BASE_URL}/libraries", json=library_data)
        response.raise_for_status()
        library = response.json()
        library_id = library["id"]
        print(f"✓ Created library: {library['name']} (ID: {library_id})")
        
        # 2. Add some chunks
        print("\n2. Adding chunks to library...")
        chunks_data = [
            {
                "text": "Machine learning is a subset of artificial intelligence.",
                "metadata": {
                    "source": "textbook",
                    "page": 42,
                    "author": "John Doe",
                    "tags": ["ml", "ai"]
                }
            },
            {
                "text": "Deep learning uses neural networks with multiple layers.",
                "metadata": {
                    "source": "textbook",
                    "page": 45,
                    "author": "John Doe",
                    "tags": ["dl", "neural-networks"]
                }
            },
            {
                "text": "Natural language processing enables computers to understand text.",
                "metadata": {
                    "source": "research-paper",
                    "page": 1,
                    "author": "Jane Smith",
                    "tags": ["nlp", "text"]
                }
            },
            {
                "text": "Vector databases store and search high-dimensional vectors efficiently.",
                "metadata": {
                    "source": "article",
                    "page": None,
                    "author": "Alice Johnson",
                    "tags": ["vectordb", "search"]
                }
            },
        ]
        
        chunk_ids = []
        for chunk_data in chunks_data:
            chunk_data["embedding"] = create_embedding(chunk_data["text"])
            response = client.post(
                f"{API_BASE_URL}/libraries/{library_id}/chunks",
                json=chunk_data
            )
            response.raise_for_status()
            chunk = response.json()
            chunk_ids.append(chunk["id"])
            print(f"✓ Added chunk: {chunk['text'][:50]}...")
        
        # 3. List all chunks
        print("\n3. Listing all chunks in library...")
        response = client.get(f"{API_BASE_URL}/libraries/{library_id}/chunks")
        response.raise_for_status()
        chunks = response.json()
        print(f"✓ Found {len(chunks)} chunks in library")
        
        # 4. Search for similar chunks
        print("\n4. Searching for similar chunks...")
        query_text = "What is machine learning?"
        query_embedding = create_embedding(query_text)
        
        search_data = {
            "embedding": query_embedding,
            "k": 3
        }
        
        response = client.post(
            f"{API_BASE_URL}/libraries/{library_id}/search",
            json=search_data
        )
        response.raise_for_status()
        results = response.json()
        
        print(f"\nQuery: '{query_text}'")
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.4f}")
            print(f"   Text: {result['chunk']['text'][:60]}...")
            print(f"   Source: {result['chunk']['metadata']['source']}")
        
        # 5. Search with metadata filter
        print("\n5. Searching with metadata filter (source='textbook')...")
        search_data["filters"] = {"source": "textbook"}
        
        response = client.post(
            f"{API_BASE_URL}/libraries/{library_id}/search",
            json=search_data
        )
        response.raise_for_status()
        results = response.json()
        
        print(f"Found {len(results)} results from textbooks:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['chunk']['text'][:60]}...")
        
        # 6. Update a chunk
        print("\n6. Updating a chunk...")
        chunk_id = chunk_ids[0]
        update_data = {
            "text": "Machine learning is a powerful subset of artificial intelligence that learns from data.",
            "embedding": create_embedding("Machine learning is a powerful subset of artificial intelligence that learns from data.")
        }
        
        response = client.put(
            f"{API_BASE_URL}/libraries/{library_id}/chunks/{chunk_id}",
            json=update_data
        )
        response.raise_for_status()
        print("✓ Chunk updated successfully")
        
        # 7. Get library details
        print("\n7. Getting library details...")
        response = client.get(f"{API_BASE_URL}/libraries/{library_id}")
        response.raise_for_status()
        library = response.json()
        print(f"✓ Library: {library['name']}")
        print(f"  Index type: {library['index_type']}")
        print(f"  Documents: {len(library['documents'])}")
        
        # 8. List all libraries
        print("\n8. Listing all libraries...")
        response = client.get(f"{API_BASE_URL}/libraries")
        response.raise_for_status()
        libraries = response.json()
        print(f"✓ Found {len(libraries)} libraries")
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    main()
