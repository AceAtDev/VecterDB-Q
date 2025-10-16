"""
Quick Test Script - Simple verification of VectorDB-Q API
Run this after starting the Docker container to verify everything works.
"""
import requests
import sys

BASE_URL = "http://localhost:8000"

def test():
    print("=" * 60)
    print("🧪 VectorDB-Q - Quick Test")
    print("=" * 60)
    
    try:
        # Test 1: Health Check
        print("\n1️⃣  Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        print("   ✅ Health check passed")
        
        # Test 2: Create Library
        print("\n2️⃣  Creating library...")
        response = requests.post(
            f"{BASE_URL}/api/v1/libraries",
            json={"name": "Quick Test", "index_type": "flat"},
            timeout=5
        )
        assert response.status_code == 201
        library_id = response.json()["id"]
        print(f"   ✅ Library created: {library_id}")
        
        # Test 3: Add Chunk
        print("\n3️⃣  Adding chunk...")
        response = requests.post(
            f"{BASE_URL}/api/v1/libraries/{library_id}/chunks",
            json={
                "text": "Test chunk",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "metadata": {"source": "test"}
            },
            timeout=5
        )
        assert response.status_code == 201
        chunk_id = response.json()["id"]
        print(f"   ✅ Chunk added: {chunk_id}")
        
        # Test 4: Search
        print("\n4️⃣  Searching...")
        response = requests.post(
            f"{BASE_URL}/api/v1/libraries/{library_id}/search",
            json={
                "embedding": [0.11, 0.19, 0.31, 0.39, 0.51],
                "k": 5,
                "metric": "cosine"
            },
            timeout=5
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        print(f"   ✅ Search returned {len(results)} result(s)")
        
        # Test 5: Cleanup
        print("\n5️⃣  Cleaning up...")
        response = requests.delete(
            f"{BASE_URL}/api/v1/libraries/{library_id}",
            timeout=5
        )
        assert response.status_code == 204
        print("   ✅ Library deleted")
        
        # Success!
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n💡 Your API is working correctly!")
        print(f"📚 View API docs: {BASE_URL}/docs")
        print(f"🔍 Run full demo: python demo_mvp.py")
        print()
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API")
        print(f"   Is the server running at {BASE_URL}?")
        print("   Start it with: docker-compose up")
        return 1
        
    except AssertionError as e:
        print(f"\n❌ ERROR: Test failed")
        print(f"   {str(e)}")
        return 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(test())
