#!/usr/bin/env python3
import sys
import os

# Add parent directory and backend directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(parent_dir, 'backend')
sys.path.insert(0, parent_dir)
sys.path.insert(0, backend_dir)

from backend.config import config
from backend.rag_system import RAGSystem

def main():
    print("Testing AI generator...")
    
    # Initialize RAG system
    rag_system = RAGSystem(config)
    
    # Test the full query flow
    print("Testing full query: 'What is MCP?'")
    try:
        answer, sources = rag_system.query("What is MCP?")
        print(f"Answer: {answer}")
        print(f"Sources: {sources}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()