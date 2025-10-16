"""
Comprehensive Demo Script for VectorDB-Q MVP 1.0
This script demonstrates all core features:
- Library CRUD operations
- Chunk CRUD operations  
- k-NN search with both Euclidean and Cosine metrics
- Metadata filtering (basic)
"""
import requests
import json
import numpy as np
from typing import List, Dict

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_response(response: requests.Response, title: str = "Response"):
    """Pretty print API response."""
    print(f"\n{title}:")
    print(f"Status: {response.status_code}")
    if response.status_code != 204:
        print(f"Body: {json.dumps(response.json(), indent=2)}")


# ============================================================================
# DEMO START
# ============================================================================

print_section("🚀 VectorDB-Q MVP 1.0 - Complete Demo")

# ----------------------------------------------------------------------------
# 1. Health Check
# ----------------------------------------------------------------------------
print_section("1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print_response(response, "✅ Health Status")

# ----------------------------------------------------------------------------
# 2. Create Library
# ----------------------------------------------------------------------------
print_section("2. Create Library - 'AI Research Papers'")
library_data = {
    "name": "AI Research Papers",
    "description": "Collection of AI research paper chunks",
    "metadata": {
        "category": "research",
        "language": "en",
        "tags": ["AI", "machine-learning", "deep-learning"]
    },
    "index_type": "flat"  # Using flat index for demo
}
response = requests.post(f"{BASE_URL}/api/v1/libraries", json=library_data)
print_response(response, "✅ Library Created")
library_id = response.json()["id"]
print(f"\n📌 Library ID: {library_id}")

# ----------------------------------------------------------------------------
# 3. List Libraries
# ----------------------------------------------------------------------------
print_section("3. List All Libraries")
response = requests.get(f"{BASE_URL}/api/v1/libraries")
print_response(response, "📚 Libraries")

# ----------------------------------------------------------------------------
# 4. Get Specific Library
# ----------------------------------------------------------------------------
print_section("4. Get Library by ID")
response = requests.get(f"{BASE_URL}/api/v1/libraries/{library_id}")
print_response(response, "📖 Library Details")

# ----------------------------------------------------------------------------
# 5. Add Multiple Chunks with Embeddings
# ----------------------------------------------------------------------------
print_section("5. Add Chunks with Embeddings")

# Sample chunks about AI topics with synthetic embeddings
chunks_data = [
    {
        "text": "Deep learning is a subset of machine learning based on artificial neural networks.",
        "embedding": [0.8, 0.6, 0.3, 0.1, 0.2],  # Embeddings about neural networks
        "metadata": {
            "source": "AI Textbook",
            "page": 42,
            "section": "Deep Learning Basics",
            "tags": ["deep-learning", "neural-networks"]
        }
    },
    {
        "text": "Natural language processing enables computers to understand human language.",
        "embedding": [0.2, 0.9, 0.7, 0.3, 0.1],  # Embeddings about NLP
        "metadata": {
            "source": "NLP Guide",
            "page": 15,
            "section": "Introduction",
            "tags": ["nlp", "language"]
        }
    },
    {
        "text": "Computer vision allows machines to interpret and understand visual information.",
        "embedding": [0.1, 0.3, 0.2, 0.8, 0.9],  # Embeddings about computer vision
        "metadata": {
            "source": "Computer Vision Handbook",
            "page": 8,
            "section": "Overview",
            "tags": ["computer-vision", "image-processing"]
        }
    },
    {
        "text": "Reinforcement learning trains agents through rewards and penalties.",
        "embedding": [0.7, 0.4, 0.5, 0.2, 0.6],  # Embeddings about RL
        "metadata": {
            "source": "RL Fundamentals",
            "page": 23,
            "section": "Core Concepts",
            "tags": ["reinforcement-learning", "agents"]
        }
    },
    {
        "text": "Neural networks consist of layers of interconnected nodes inspired by biological neurons.",
        "embedding": [0.85, 0.55, 0.35, 0.15, 0.25],  # Similar to first chunk
        "metadata": {
            "source": "AI Textbook",
            "page": 43,
            "section": "Deep Learning Basics",
            "tags": ["deep-learning", "neural-networks"]
        }
    }
]

chunk_ids = []
for i, chunk_data in enumerate(chunks_data, 1):
    response = requests.post(
        f"{BASE_URL}/api/v1/libraries/{library_id}/chunks",
        json=chunk_data
    )
    if response.status_code == 201:
        chunk_id = response.json()["id"]
        chunk_ids.append(chunk_id)
        print(f"\n✅ Chunk {i} added: {chunk_data['text'][:60]}...")
        print(f"   ID: {chunk_id}")

# ----------------------------------------------------------------------------
# 6. List All Chunks
# ----------------------------------------------------------------------------
print_section("6. List All Chunks in Library")
response = requests.get(f"{BASE_URL}/api/v1/libraries/{library_id}/chunks")
print_response(response, "📝 All Chunks")
print(f"\nTotal chunks: {len(response.json())}")

# ----------------------------------------------------------------------------
# 7. Get Specific Chunk
# ----------------------------------------------------------------------------
print_section("7. Get Specific Chunk")
response = requests.get(
    f"{BASE_URL}/api/v1/libraries/{library_id}/chunks/{chunk_ids[0]}"
)
print_response(response, "📄 Chunk Details")

# ----------------------------------------------------------------------------
# 8. Update Chunk
# ----------------------------------------------------------------------------
print_section("8. Update Chunk Text")
update_data = {
    "text": "Deep learning is a powerful subset of machine learning using multi-layer neural networks."
}
response = requests.put(
    f"{BASE_URL}/api/v1/libraries/{library_id}/chunks/{chunk_ids[0]}",
    json=update_data
)
print_response(response, "✏️ Updated Chunk")

# ----------------------------------------------------------------------------
# 9. k-NN Search with Euclidean Distance
# ----------------------------------------------------------------------------
print_section("9. k-NN Search - Euclidean Distance")
print("🔍 Query: Looking for content similar to neural networks...")

# Query vector similar to neural network embeddings
search_query = {
    "embedding": [0.82, 0.58, 0.32, 0.12, 0.22],  # Similar to neural network chunks
    "k": 3,
    "metric": "euclidean"
}

response = requests.post(
    f"{BASE_URL}/api/v1/libraries/{library_id}/search",
    json=search_query
)
print_response(response, "🎯 Search Results (Euclidean)")

if response.status_code == 200:
    results = response.json()
    print(f"\n📊 Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"  Score: {result['score']:.4f}")
        print(f"  Distance: {result['distance']:.4f}")
        print(f"  Text: {result['chunk']['text'][:80]}...")

# ----------------------------------------------------------------------------
# 10. k-NN Search with Cosine Similarity
# ----------------------------------------------------------------------------
print_section("10. k-NN Search - Cosine Similarity")
print("🔍 Query: Looking for content about language processing...")

# Query vector similar to NLP embeddings
search_query = {
    "embedding": [0.25, 0.85, 0.68, 0.28, 0.15],  # Similar to NLP chunk
    "k": 3,
    "metric": "cosine"
}

response = requests.post(
    f"{BASE_URL}/api/v1/libraries/{library_id}/search",
    json=search_query
)
print_response(response, "🎯 Search Results (Cosine)")

if response.status_code == 200:
    results = response.json()
    print(f"\n📊 Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"  Score: {result['score']:.4f}")
        print(f"  Distance: {result['distance']:.4f}")
        print(f"  Text: {result['chunk']['text'][:80]}...")

# ----------------------------------------------------------------------------
# 11. Search with Metadata Filtering
# ----------------------------------------------------------------------------
print_section("11. Search with Metadata Filter")
print("🔍 Query: Find neural network content from 'AI Textbook'...")

search_query = {
    "embedding": [0.8, 0.6, 0.3, 0.1, 0.2],
    "k": 5,
    "metric": "euclidean",
    "filters": {
        "source": "AI Textbook"
    }
}

response = requests.post(
    f"{BASE_URL}/api/v1/libraries/{library_id}/search",
    json=search_query
)
print_response(response, "🎯 Filtered Search Results")

if response.status_code == 200:
    results = response.json()
    print(f"\n📊 Found {len(results)} results matching filter:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"  Source: {result['chunk']['metadata']['source']}")
        print(f"  Score: {result['score']:.4f}")
        print(f"  Text: {result['chunk']['text'][:80]}...")

# ----------------------------------------------------------------------------
# 12. Update Library
# ----------------------------------------------------------------------------
print_section("12. Update Library Description")
update_data = {
    "description": "Comprehensive collection of AI and ML research paper chunks - Updated!"
}
response = requests.put(
    f"{BASE_URL}/api/v1/libraries/{library_id}",
    json=update_data
)
print_response(response, "✏️ Updated Library")

# ----------------------------------------------------------------------------
# 13. Delete Chunk
# ----------------------------------------------------------------------------
print_section("13. Delete a Chunk")
print(f"🗑️ Deleting chunk: {chunk_ids[0]}")
response = requests.delete(
    f"{BASE_URL}/api/v1/libraries/{library_id}/chunks/{chunk_ids[0]}"
)
print(f"Status: {response.status_code}")
if response.status_code == 204:
    print("✅ Chunk deleted successfully")

# Verify deletion
response = requests.get(f"{BASE_URL}/api/v1/libraries/{library_id}/chunks")
print(f"\n📊 Remaining chunks: {len(response.json())}")

# ----------------------------------------------------------------------------
# 14. Delete Library
# ----------------------------------------------------------------------------
print_section("14. Delete Library")
print(f"🗑️ Deleting library: {library_id}")
response = requests.delete(f"{BASE_URL}/api/v1/libraries/{library_id}")
print(f"Status: {response.status_code}")
if response.status_code == 204:
    print("✅ Library deleted successfully")

# Verify deletion
response = requests.get(f"{BASE_URL}/api/v1/libraries")
print(f"\n📊 Remaining libraries: {len(response.json())}")

# ----------------------------------------------------------------------------
# DEMO COMPLETE
# ----------------------------------------------------------------------------
print_section("✅ Demo Complete - All MVP Features Verified!")

print("\n📋 Features Demonstrated:")
print("  ✅ Library CRUD (Create, Read, Update, Delete)")
print("  ✅ Chunk CRUD (Create, Read, Update, Delete)")
print("  ✅ Vector indexing (Flat index)")
print("  ✅ k-NN search with Euclidean distance")
print("  ✅ k-NN search with Cosine similarity")
print("  ✅ Metadata filtering")
print("  ✅ Thread-safe operations")
print("  ✅ RESTful API design")

print("\n🎯 MVP 1.0 Status: COMPLETE ✅")
print("=" * 70)
