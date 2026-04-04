"""Integration tests for the /api/system endpoints."""


def test_system_status(client):
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "gemini_available" in data
    assert "neo4j_available" in data
    assert "chat_provider" in data
    assert "chat_model" in data
