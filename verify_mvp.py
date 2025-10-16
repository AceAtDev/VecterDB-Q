"""Quick test script to verify MVP 1.0 functionality."""
import requests
import json
from typing import List

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print(f"✅ Health check: {response.json()}")


def test_create_library():
    """Test library creation."""
    print("\n📚 Testing library creation...")
    library_data = {
        "name": "Test Library",
        "description": "A test library for MVP verification",
        "metadata": {
            "category": "test",
            "language": "en",
            "tags": ["test", "mvp"]
        },
        "index_type": "flat"
    }
    response = requests.post(f"{BASE_URL}/api/v1/libraries", json=library_data)
    assert response.status_code == 201
    library = response.json()
    print(f"✅ Library created: {library['id']}")
    return library['id']


def test_list_libraries():
    """Test listing libraries."""
    print("\n📋 Testing library listing...")
    response = requests.get(f"{BASE_URL}/api/v1/libraries")
    assert response.status_code == 200
    libraries = response.json()
    print(f"✅ Found {len(libraries)} library(ies)")
    return libraries


def test_get_library(library_id: str):
    """Test getting a specific library."""
    print(f"\n🔍 Testing get library {library_id}...")
    response = requests.get(f"{BASE_URL}/api/v1/libraries/{library_id}")
    assert response.status_code == 200
    library = response.json()
    print(f"✅ Library retrieved: {library['name']}")
    return library


def test_create_chunk(library_id: str):
    """Test chunk creation."""
    print(f"\n📝 Testing chunk creation in library {library_id}...")
    chunk_data = {
        "text": "This is a test chunk for MVP verification.",
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],  # Dummy 5D embedding
        "metadata": {
            "source": "test_script",
            "page": 1,
            "tags": ["test"]
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/libraries/{library_id}/chunks",
        json=chunk_data
    )
    assert response.status_code == 201
    chunk = response.json()
    print(f"✅ Chunk created: {chunk['id']}")
    return chunk['id']


def test_list_chunks(library_id: str):
    """Test listing chunks."""
    print(f"\n📋 Testing chunk listing in library {library_id}...")
    response = requests.get(f"{BASE_URL}/api/v1/libraries/{library_id}/chunks")
    assert response.status_code == 200
    chunks = response.json()
    print(f"✅ Found {len(chunks)} chunk(s)")
    return chunks


def test_search(library_id: str):
    """Test k-NN search."""
    print(f"\n🔎 Testing k-NN search in library {library_id}...")
    search_data = {
        "embedding": [0.11, 0.19, 0.31, 0.39, 0.51],  # Similar to our test chunk
        "k": 5
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/libraries/{library_id}/search",
        json=search_data
    )
    assert response.status_code == 200
    results = response.json()
    print(f"✅ Found {len(results)} result(s)")
    if results:
        print(f"   Top result score: {results[0]['score']:.4f}")
    return results


def test_update_library(library_id: str):
    """Test library update."""
    print(f"\n✏️ Testing library update {library_id}...")
    update_data = {
        "description": "Updated description for MVP test"
    }
    response = requests.put(
        f"{BASE_URL}/api/v1/libraries/{library_id}",
        json=update_data
    )
    assert response.status_code == 200
    library = response.json()
    print(f"✅ Library updated: {library['description']}")


def test_delete_chunk(library_id: str, chunk_id: str):
    """Test chunk deletion."""
    print(f"\n🗑️ Testing chunk deletion {chunk_id}...")
    response = requests.delete(
        f"{BASE_URL}/api/v1/libraries/{library_id}/chunks/{chunk_id}"
    )
    assert response.status_code == 204
    print(f"✅ Chunk deleted")


def test_delete_library(library_id: str):
    """Test library deletion."""
    print(f"\n🗑️ Testing library deletion {library_id}...")
    response = requests.delete(f"{BASE_URL}/api/v1/libraries/{library_id}")
    assert response.status_code == 204
    print(f"✅ Library deleted")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 MVP 1.0 Functionality Verification")
    print("=" * 60)
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Create library
        library_id = test_create_library()
        
        # Test 3: List libraries
        test_list_libraries()
        
        # Test 4: Get specific library
        test_get_library(library_id)
        
        # Test 5: Create multiple chunks
        chunk_ids = []
        for i in range(3):
            chunk_id = test_create_chunk(library_id)
            chunk_ids.append(chunk_id)
        
        # Test 6: List chunks
        test_list_chunks(library_id)
        
        # Test 7: Search
        test_search(library_id)
        
        # Test 8: Update library
        test_update_library(library_id)
        
        # Test 9: Delete a chunk
        test_delete_chunk(library_id, chunk_ids[0])
        
        # Test 10: Verify chunk deletion
        remaining_chunks = test_list_chunks(library_id)
        assert len(remaining_chunks) == 2
        
        # Test 11: Delete library
        test_delete_library(library_id)
        
        print("\n" + "=" * 60)
        print("✅ All MVP 1.0 tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection error. Is the server running at http://localhost:8000?")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
