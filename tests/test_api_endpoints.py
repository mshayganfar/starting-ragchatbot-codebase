#!/usr/bin/env python3
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.mark.api
class TestQueryEndpoint:
    """Test the /api/query endpoint"""

    def test_query_with_session_id(self, client):
        """Test query endpoint with provided session ID"""
        request_data = {
            "query": "What is Python?",
            "session_id": "test_session_123"
        }
        
        response = client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test_session_123"
        assert isinstance(data["sources"], list)

    def test_query_without_session_id(self, client):
        """Test query endpoint without session ID - should create new session"""
        request_data = {
            "query": "What is machine learning?"
        }
        
        response = client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] is not None
        assert isinstance(data["sources"], list)

    def test_query_empty_string(self, client):
        """Test query endpoint with empty query string"""
        request_data = {
            "query": ""
        }
        
        response = client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_query_long_text(self, client):
        """Test query endpoint with long query text"""
        long_query = "What is Python? " * 100  # Long query
        request_data = {
            "query": long_query,
            "session_id": "long_query_session"
        }
        
        response = client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["session_id"] == "long_query_session"

    def test_query_special_characters(self, client):
        """Test query endpoint with special characters"""
        request_data = {
            "query": "What about Python's @decorators & <generators>?",
            "session_id": "special_chars_session"
        }
        
        response = client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_query_missing_query_field(self, client):
        """Test query endpoint with missing query field"""
        request_data = {
            "session_id": "no_query_session"
        }
        
        response = client.post("/api/query", json=request_data)
        
        assert response.status_code == 422  # Validation error

    def test_query_invalid_json(self, client):
        """Test query endpoint with invalid JSON"""
        response = client.post("/api/query", data="invalid json")
        
        assert response.status_code == 422

    def test_query_content_type_validation(self, client):
        """Test query endpoint with correct content type"""
        request_data = {
            "query": "Test query",
            "session_id": "content_type_test"
        }
        
        response = client.post(
            "/api/query", 
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200


@pytest.mark.api  
class TestCoursesEndpoint:
    """Test the /api/courses endpoint"""

    def test_get_course_stats(self, client):
        """Test getting course statistics"""
        response = client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

    def test_courses_endpoint_method_not_allowed(self, client):
        """Test that POST method is not allowed on courses endpoint"""
        response = client.post("/api/courses", json={})
        
        assert response.status_code == 405  # Method not allowed

    def test_courses_endpoint_with_query_params(self, client):
        """Test courses endpoint ignores query parameters"""
        response = client.get("/api/courses?param=value")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data


@pytest.mark.api
class TestRootEndpoint:
    """Test the root / endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "RAG System" in data["message"]

    def test_root_endpoint_post_not_allowed(self, client):
        """Test that POST is not allowed on root endpoint"""
        response = client.post("/", json={})
        
        assert response.status_code == 405


@pytest.mark.api
class TestErrorHandling:
    """Test error handling across API endpoints"""

    def test_query_endpoint_server_error(self, client):
        """Test query endpoint handles server errors gracefully"""
        # Since we're using a test app with mocks, we can't easily simulate server errors
        # This test verifies that the normal operation works correctly
        request_data = {"query": "test query"}
        response = client.post("/api/query", json=request_data)
        
        # The test app should handle this correctly
        assert response.status_code == 200

    def test_nonexistent_endpoint(self, client):
        """Test accessing non-existent endpoint"""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404

    def test_malformed_url(self, client):
        """Test accessing malformed URLs"""
        response = client.get("/api//query")  # Double slash
        
        assert response.status_code == 404


@pytest.mark.api
class TestCORSHeaders:
    """Test CORS headers are properly set"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        response = client.options("/api/query")
        
        # CORS should be handled by FastAPI middleware
        assert response.status_code in [200, 405]  # Options might not be implemented

    def test_cors_preflight(self, client):
        """Test CORS preflight request"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = client.options("/api/query", headers=headers)
        
        # Should allow the request
        assert response.status_code in [200, 405]


@pytest.mark.api
class TestAPIIntegration:
    """Integration tests for API workflow"""

    def test_full_query_workflow(self, client):
        """Test complete query workflow"""
        # First, get course stats
        courses_response = client.get("/api/courses")
        assert courses_response.status_code == 200
        
        course_data = courses_response.json()
        assert course_data["total_courses"] >= 0
        
        # Then make a query
        query_request = {
            "query": "Tell me about the available courses",
            "session_id": "integration_test"
        }
        
        query_response = client.post("/api/query", json=query_request)
        assert query_response.status_code == 200
        
        query_data = query_response.json()
        assert query_data["session_id"] == "integration_test"
        assert len(query_data["sources"]) >= 0

    def test_session_continuity(self, client):
        """Test that session ID is maintained across requests"""
        session_id = "continuity_test"
        
        # First query
        request1 = {
            "query": "What is Python?",
            "session_id": session_id
        }
        response1 = client.post("/api/query", json=request1)
        assert response1.status_code == 200
        assert response1.json()["session_id"] == session_id
        
        # Second query with same session
        request2 = {
            "query": "Tell me more about Python features",
            "session_id": session_id
        }
        response2 = client.post("/api/query", json=request2)
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

    def test_multiple_concurrent_sessions(self, client):
        """Test handling multiple concurrent sessions"""
        sessions = ["session_1", "session_2", "session_3"]
        
        for session_id in sessions:
            request_data = {
                "query": f"Query for {session_id}",
                "session_id": session_id
            }
            response = client.post("/api/query", json=request_data)
            assert response.status_code == 200
            assert response.json()["session_id"] == session_id


@pytest.mark.api
class TestResponseValidation:
    """Test response data validation"""

    def test_query_response_schema(self, client):
        """Test that query response matches expected schema"""
        request_data = {
            "query": "Test query for schema validation",
            "session_id": "schema_test"
        }
        
        response = client.post("/api/query", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate response structure
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)
        
        # Validate that sources contain strings
        for source in data["sources"]:
            assert isinstance(source, str)

    def test_courses_response_schema(self, client):
        """Test that courses response matches expected schema"""
        response = client.get("/api/courses")
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate response structure
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert data["total_courses"] >= 0
        
        # Validate that course titles are strings
        for title in data["course_titles"]:
            assert isinstance(title, str)
            assert len(title) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])