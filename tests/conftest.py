#!/usr/bin/env python3
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from typing import Dict, Any, List

# Add parent directory and backend directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(parent_dir, 'backend')
sys.path.insert(0, parent_dir)
sys.path.insert(0, backend_dir)


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    mock_config = Mock()
    mock_config.anthropic_api_key = "test_api_key"
    mock_config.model_name = "claude-sonnet-4-20250514"
    mock_config.chunk_size = 800
    mock_config.chunk_overlap = 100
    mock_config.max_search_results = 5
    mock_config.embedding_model = "all-MiniLM-L6-v2"
    return mock_config


@pytest.fixture
def mock_rag_system():
    """Mock RAG system for API testing"""
    mock_rag = Mock()
    mock_rag.query.return_value = ("Test answer", ["Source 1", "Source 2"])
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"]
    }
    mock_rag.session_manager = Mock()
    mock_rag.session_manager.create_session.return_value = "test_session_id"
    return mock_rag


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    mock_store = Mock()
    mock_store.search.return_value = [
        {"content": "Test content 1", "metadata": {"course": "Course A"}},
        {"content": "Test content 2", "metadata": {"course": "Course B"}}
    ]
    mock_store.get_course_names.return_value = ["Course A", "Course B"]
    return mock_store


@pytest.fixture
def mock_ai_generator():
    """Mock AI generator for testing"""
    mock_gen = Mock()
    mock_gen.generate_response.return_value = "Test AI response"
    return mock_gen


@pytest.fixture
def sample_query_request():
    """Sample query request data for testing"""
    return {
        "query": "What is the main topic of Course A?",
        "session_id": "test_session_123"
    }


@pytest.fixture
def sample_query_response():
    """Sample query response data for testing"""
    return {
        "answer": "Course A covers advanced Python programming concepts.",
        "sources": ["Course A Lesson 1", "Course A Lesson 2"],
        "session_id": "test_session_123"
    }


@pytest.fixture
def sample_course_stats():
    """Sample course statistics for testing"""
    return {
        "total_courses": 3,
        "course_titles": ["Python Basics", "Advanced Python", "Web Development"]
    }


@pytest.fixture
def test_app():
    """Create a test FastAPI app without static file mounting to avoid directory issues"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional
    
    # Create a minimal app for testing
    app = FastAPI(title="Test RAG System")
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mock RAG system for the app
    mock_rag = Mock()
    mock_rag.query.return_value = ("Test answer", ["Source 1"])
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 1,
        "course_titles": ["Test Course"]
    }
    mock_rag.session_manager = Mock()
    mock_rag.session_manager.create_session.return_value = "test_session"
    
    # Pydantic models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]
    
    # API Endpoints
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id or mock_rag.session_manager.create_session()
            answer, sources = mock_rag.query(request.query, session_id)
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/")
    async def root():
        return {"message": "Course Materials RAG System"}
    
    return app


@pytest.fixture
def client(test_app):
    """Test client for API testing"""
    return TestClient(test_app)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for AI generator testing"""
    mock_client = Mock()
    
    # Mock response structure
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response")]
    mock_response.stop_reason = "stop"
    
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing"""
    mock_session = Mock()
    mock_session.create_session.return_value = "test_session_123"
    mock_session.add_to_history.return_value = None
    mock_session.get_conversation_context.return_value = "Previous conversation context"
    return mock_session


@pytest.fixture
def sample_course_data():
    """Sample course data for testing"""
    return {
        "courses": [
            {
                "title": "Python Fundamentals",
                "instructor": "John Doe", 
                "course_link": "https://example.com/python-fundamentals",
                "lessons": [
                    {"number": 1, "title": "Introduction to Python", "lesson_link": "https://example.com/lesson1"},
                    {"number": 2, "title": "Variables and Data Types", "lesson_link": "https://example.com/lesson2"}
                ]
            },
            {
                "title": "Advanced Python",
                "instructor": "Jane Smith",
                "course_link": "https://example.com/advanced-python", 
                "lessons": [
                    {"number": 1, "title": "Decorators", "lesson_link": "https://example.com/advanced1"},
                    {"number": 2, "title": "Generators", "lesson_link": "https://example.com/advanced2"}
                ]
            }
        ]
    }


@pytest.fixture
def sample_document_content():
    """Sample document content for testing"""
    return """Course Title: Python Fundamentals
Course Link: https://example.com/python-fundamentals  
Course Instructor: John Doe

Lesson 1: Introduction to Python
Welcome to Python programming. Python is a versatile programming language.

Lesson 2: Variables and Data Types
In Python, variables are containers for storing data values. Python has various data types.
"""


@pytest.fixture(autouse=True)
def cleanup_warnings():
    """Auto-use fixture to suppress warnings during tests"""
    import warnings
    warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")
    yield
    warnings.resetwarnings()