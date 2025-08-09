#!/usr/bin/env python3
import sys
import os
sys.path.append('./backend')

from backend.config import config
from backend.vector_store import VectorStore

def main():
    print("Testing course name resolution...")
    
    # Create vector store instance
    vector_store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)
    
    # Test course name resolution
    test_queries = [
        "MCP: Build Rich-Context AI Apps with Anthropic",
        "MCP",
        "Build Rich-Context AI Apps",
        "Anthropic",
        "Building Towards Computer Use",
        "Computer Use",
        "Chroma",
        "Advanced Retrieval for AI with Chroma"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        result = vector_store._resolve_course_name(query)
        print(f"Resolved to: {result}")

if __name__ == "__main__":
    main()