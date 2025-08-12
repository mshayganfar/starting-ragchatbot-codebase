#!/usr/bin/env python3
import os
import sys

# Add parent directory and backend directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(parent_dir, "backend")
sys.path.insert(0, parent_dir)
sys.path.insert(0, backend_dir)

from backend.config import config
from backend.rag_system import RAGSystem


def main():
    print("Testing search functionality...")

    # Initialize RAG system
    rag_system = RAGSystem(config)

    # Test the search tool directly
    search_tool = rag_system.search_tool

    # Test 1: Search with exact course title
    print("\nTest 1: Exact course title")
    result = search_tool.execute(
        query="What is MCP?",
        course_name="MCP: Build Rich-Context AI Apps with Anthropic",
    )
    print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")

    # Test 2: Search with partial course name that should resolve
    print("\nTest 2: Partial course name")
    result = search_tool.execute(query="What is MCP?", course_name="MCP")
    print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")

    # Test 3: Direct vector store search
    print("\nTest 3: Direct vector store search")
    search_results = rag_system.vector_store.search(
        query="What is MCP?",
        course_name="MCP: Build Rich-Context AI Apps with Anthropic",
    )
    print(f"Search results error: {search_results.error}")
    print(f"Number of documents: {len(search_results.documents)}")
    if search_results.documents:
        print(f"First result: {search_results.documents[0][:200]}...")


if __name__ == "__main__":
    main()
