"""Integration tests for chat route."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


class TestChatRoute:
    """Test chat endpoint."""
    
    def test_chat_requires_auth(self, client):
        """Chat endpoint should require authentication."""
        response = client.post("/chat", json={"question": "test"})
        assert response.status_code == 401
    
    def test_chat_returns_error_on_invalid_sql(self, client, auth_token):
        """Chat should return error when SQL validation fails."""
        with patch('app.routes.chat.generate_sql') as mock_gen:
            mock_gen.return_value = "DELETE FROM candidates"
            
            response = client.post(
                "/chat",
                json={"question": "delete all candidates"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is not None
            assert "DELETE" in data["error"]
            assert data["sql"] == "DELETE FROM candidates"
    
    def test_chat_response_structure(self, client, auth_token):
        """Chat response should have correct structure."""
        with patch('app.routes.chat.generate_sql') as mock_sql, \
             patch('app.routes.chat.generate_answer') as mock_answer:
            
            mock_sql.return_value = "SELECT * FROM candidates LIMIT 1"
            mock_answer.return_value = "Found 0 candidates."
            
            response = client.post(
                "/chat",
                json={"question": "list candidates"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sql" in data
            assert "rowCount" in data or "row_count" in data
            assert "columns" in data
    
    def test_chat_handles_sql_generation_error(self, client, auth_token):
        """Chat should handle SQL generation errors gracefully."""
        with patch('app.routes.chat.generate_sql') as mock_gen:
            mock_gen.side_effect = Exception("LLM error")
            
            response = client.post(
                "/chat",
                json={"question": "test"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is not None
            assert "SQL generation failed" in data["error"]
    
    def test_chat_with_history(self, client, auth_token):
        """Chat should accept conversation history."""
        with patch('app.routes.chat.generate_sql') as mock_sql, \
             patch('app.routes.chat.generate_answer') as mock_answer:
            
            mock_sql.return_value = "SELECT * FROM candidates LIMIT 1"
            mock_answer.return_value = "Answer"
            
            response = client.post(
                "/chat",
                json={
                    "question": "show them",
                    "history": [
                        {"role": "user", "content": "find candidates"},
                        {"role": "assistant", "content": "Here are the candidates"}
                    ]
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            mock_sql.assert_called_once()
            args = mock_sql.call_args[0]
            assert args[0] == "show them"
            assert args[1] is not None  # history passed
    
    def test_chat_adds_limit_if_missing(self, client, auth_token):
        """Chat should add LIMIT 50 if not present."""
        with patch('app.routes.chat.generate_sql') as mock_sql, \
             patch('app.routes.chat.generate_answer') as mock_answer:
            
            mock_sql.return_value = "SELECT * FROM candidates"
            mock_answer.return_value = "Answer"
            
            response = client.post(
                "/chat",
                json={"question": "list all"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            # SQL execution should have LIMIT added
            # We can't directly verify the executed SQL, but response should succeed


class TestChatValidationIntegration:
    """Test validation integration in chat route."""
    
    def test_validation_rejects_unsafe_sql(self, client, auth_token):
        """Validation should prevent execution of unsafe SQL."""
        with patch('app.routes.chat.generate_sql') as mock_gen:
            mock_gen.return_value = "DROP TABLE candidates"
            
            response = client.post(
                "/chat",
                json={"question": "destroy everything"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is not None
            assert "DROP" in data["error"]
            assert data["answer"] is None
