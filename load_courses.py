#!/usr/bin/env python3
"""Script to manually load course documents into the vector store"""

import sys
import os
sys.path.append('./backend')

# Set environment variables to handle numpy compatibility
os.environ['NUMPY_EXPERIMENTAL_ARRAY_API'] = '0'

try:
    from backend.config import config
    from backend.rag_system import RAGSystem
    
    def main():
        print("Loading course documents...")
        
        # Initialize RAG system
        rag_system = RAGSystem(config)
        
        # Load courses from docs folder
        docs_path = "./docs"
        if os.path.exists(docs_path):
            print(f"Loading documents from {docs_path}")
            try:
                courses, chunks = rag_system.add_course_folder(docs_path, clear_existing=True)
                print(f"Successfully loaded {courses} courses with {chunks} chunks")
                
                # Verify the courses were loaded
                analytics = rag_system.get_course_analytics()
                print(f"Total courses in system: {analytics['total_courses']}")
                print("Available courses:")
                for title in analytics['course_titles']:
                    print(f"  - {title}")
                    
                # Test search for the specific course
                print("\nTesting course name resolution...")
                result = rag_system.vector_store._resolve_course_name("MCP: Build Rich-Context AI Apps with Anthropic")
                print(f"Resolved course name: {result}")
                
            except Exception as e:
                print(f"Error loading documents: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Docs directory {docs_path} does not exist")
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory and dependencies are installed")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()