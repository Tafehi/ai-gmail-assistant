from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestAPIEndpoints:
    def test_root_serves_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "AI Gmail Assistant" in response.text

    def test_providers_endpoint(self):
        response = client.get("/api/providers")
        assert response.status_code == 200
        data = response.json()
        assert "OpenAI" in data
        assert "Anthropic" in data
        assert "AWS Bedrock" in data
        assert "Azure OpenAI" in data
        assert "models" in data["Anthropic"]
        assert len(data["Anthropic"]["models"]) > 0

    def test_status_endpoint(self):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "gmail_authenticated" in data
        assert isinstance(data["gmail_authenticated"], bool)

    def test_chat_missing_credentials(self):
        response = client.post("/api/chat", json={
            "message": "hello",
            "provider": "OpenAI",
            "model": "gpt-4o",
            "history": [],
        })
        assert response.status_code == 200
        data = response.json()
        assert "error" in data or "response" in data

    def test_chat_invalid_provider(self):
        response = client.post("/api/chat", json={
            "message": "hello",
            "provider": "InvalidProvider",
            "model": "fake-model",
            "history": [],
        })
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
