#!/usr/bin/env python3

import os
import sys

from backend.rag_system import RAGSystem

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Initialize RAG system
rag = RAGSystem()

# Check what courses are available
try:
    # Get all course metadata from the course_catalog collection
    from chromadb.utils import embedding_functions

    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Connect to ChromaDB
    import chromadb

    client = chromadb.PersistentClient(path="./backend/chroma_db")

    # Get course catalog collection
    try:
        catalog_collection = client.get_collection(
            "course_catalog", embedding_function=sentence_transformer_ef
        )
        results = catalog_collection.get()

        print("Available courses:")
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                print(f"- {doc}")
                print(f"  Metadata: {metadata}")
        else:
            print("No courses found in catalog")
    except Exception as e:
        print(f"Error accessing course catalog: {e}")

    # Also check course content collection
    try:
        content_collection = client.get_collection(
            "course_content", embedding_function=sentence_transformer_ef
        )
        content_results = content_collection.get()

        print(
            f'\nCourse content collection has {len(content_results["documents"])} chunks'
        )

        # Get unique course names from content
        course_names = set()
        if content_results["metadatas"]:
            for metadata in content_results["metadatas"]:
                if "course_name" in metadata:
                    course_names.add(metadata["course_name"])

        print("Course names in content:")
        for name in sorted(course_names):
            print(f"- {name}")

    except Exception as e:
        print(f"Error accessing course content: {e}")

except Exception as e:
    print(f"Error: {e}")
