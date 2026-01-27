def test_health_check(client):
    """Test the /health endpoint returns correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}