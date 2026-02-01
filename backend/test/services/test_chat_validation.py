"""Unit tests for SQL validation service."""

import pytest
from app.services.chat.validation import validate_sql


class TestValidateSQL:
    """Test SQL validation logic."""
    
    def test_valid_select_query(self):
        """Valid SELECT queries should pass."""
        valid, error = validate_sql("SELECT * FROM candidates")
        assert valid is True
        assert error is None
    
    def test_select_with_joins(self):
        """SELECT with JOINs should pass."""
        query = "SELECT c.* FROM candidates c JOIN positions p ON c.id = p.candidate_id"
        valid, error = validate_sql(query)
        assert valid is True
        assert error is None
    
    def test_select_with_where(self):
        """SELECT with WHERE clause should pass."""
        query = "SELECT * FROM candidates WHERE status = 'active'"
        valid, error = validate_sql(query)
        assert valid is True
        assert error is None
    
    def test_select_with_limit(self):
        """SELECT with LIMIT should pass."""
        query = "SELECT * FROM candidates LIMIT 50"
        valid, error = validate_sql(query)
        assert valid is True
        assert error is None
    
    def test_select_with_trailing_semicolon(self):
        """SELECT with trailing semicolon should pass."""
        query = "SELECT * FROM candidates;"
        valid, error = validate_sql(query)
        assert valid is True
        assert error is None
    
    def test_case_insensitive_select(self):
        """Lowercase select should pass."""
        query = "select * from candidates"
        valid, error = validate_sql(query)
        assert valid is True
        assert error is None
    
    def test_reject_insert(self):
        """INSERT statements should be rejected."""
        query = "INSERT INTO candidates (name) VALUES ('test')"
        valid, error = validate_sql(query)
        assert valid is False
        assert "INSERT" in error
    
    def test_reject_update(self):
        """UPDATE statements should be rejected."""
        query = "UPDATE candidates SET name = 'test'"
        valid, error = validate_sql(query)
        assert valid is False
        assert "UPDATE" in error
    
    def test_reject_delete(self):
        """DELETE statements should be rejected."""
        query = "DELETE FROM candidates"
        valid, error = validate_sql(query)
        assert valid is False
        assert "DELETE" in error
    
    def test_reject_drop(self):
        """DROP statements should be rejected."""
        query = "DROP TABLE candidates"
        valid, error = validate_sql(query)
        assert valid is False
        assert "DROP" in error
    
    def test_reject_alter(self):
        """ALTER statements should be rejected."""
        query = "ALTER TABLE candidates ADD COLUMN test VARCHAR(255)"
        valid, error = validate_sql(query)
        assert valid is False
        assert "ALTER" in error
    
    def test_reject_truncate(self):
        """TRUNCATE statements should be rejected."""
        query = "TRUNCATE TABLE candidates"
        valid, error = validate_sql(query)
        assert valid is False
        assert "TRUNCATE" in error
    
    def test_reject_create(self):
        """CREATE statements should be rejected."""
        query = "CREATE TABLE test (id INT)"
        valid, error = validate_sql(query)
        assert valid is False
        assert "CREATE" in error
    
    def test_reject_multiple_statements(self):
        """Multiple statements should be rejected."""
        query = "SELECT * FROM candidates; SELECT * FROM positions"
        valid, error = validate_sql(query)
        assert valid is False
        assert "Multiple statements" in error
    
    def test_reject_sql_injection_attempt(self):
        """SQL injection attempts should be rejected."""
        query = "SELECT * FROM candidates; DROP TABLE candidates"
        valid, error = validate_sql(query)
        assert valid is False
        # Should reject either for multiple statements or DROP keyword
        assert error is not None
    
    def test_reject_sql_comments(self):
        """SQL comments should be rejected."""
        query = "SELECT * FROM candidates -- comment"
        valid, error = validate_sql(query)
        assert valid is False
        assert "comment" in error.lower()
    
    def test_reject_block_comments(self):
        """Block comments should be rejected."""
        query = "SELECT * FROM /* comment */ candidates"
        valid, error = validate_sql(query)
        assert valid is False
        assert "comment" in error.lower()
    
    def test_empty_query(self):
        """Empty queries should be rejected."""
        valid, error = validate_sql("")
        assert valid is False
        assert error is not None
    
    def test_whitespace_handling(self):
        """Queries with leading/trailing whitespace should pass if valid."""
        query = "  SELECT * FROM candidates  "
        valid, error = validate_sql(query)
        assert valid is True
        assert error is None
    
    def test_column_named_insert_allowed(self):
        """Columns named 'insert' should not trigger false positive."""
        query = "SELECT insert_date FROM candidates"
        valid, error = validate_sql(query)
        assert valid is True
        assert error is None
