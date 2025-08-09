#!/usr/bin/env python3
import sys
import os
sys.path.append('./backend')

from backend.config import config
from backend.vector_store import VectorStore

def main():
    print("Debugging ChromaDB query format...")
    
    # Create vector store instance
    vector_store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)
    
    # Test the catalog query directly
    try:
        results = vector_store.course_catalog.query(
            query_texts=["MCP: Build Rich-Context AI Apps with Anthropic"],
            n_results=1
        )
        
        print("Raw ChromaDB results:")
        print(f"Type of results: {type(results)}")
        print(f"Results keys: {results.keys()}")
        
        print(f"\nDocuments: {results['documents']}")
        print(f"Type of documents: {type(results['documents'])}")
        if results['documents']:
            print(f"Type of documents[0]: {type(results['documents'][0])}")
            print(f"Documents[0]: {results['documents'][0]}")
        
        print(f"\nMetadatas: {results['metadatas']}")
        print(f"Type of metadatas: {type(results['metadatas'])}")
        if results['metadatas']:
            print(f"Type of metadatas[0]: {type(results['metadatas'][0])}")
            print(f"Metadatas[0]: {results['metadatas'][0]}")
            if results['metadatas'][0]:
                print(f"Type of metadatas[0][0]: {type(results['metadatas'][0][0])}")
                print(f"Metadatas[0][0]: {results['metadatas'][0][0]}")
                if isinstance(results['metadatas'][0][0], dict):
                    print(f"Metadatas[0][0] keys: {list(results['metadatas'][0][0].keys())}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()