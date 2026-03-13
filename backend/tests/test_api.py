"""Tests for backend.app.api.routes — FastAPI endpoints.

Uses a TestClient with a mocked HybridSearcher (see conftest.py).
"""

from fastapi.testclient import TestClient


# ── Health ───────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "commit" in data


# ── Search ───────────────────────────────────────────────────────────────────

class TestSearch:
    def test_search_valid(self, client: TestClient) -> None:
        resp = client.post("/search", json={"query": "test query"})
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0
        assert data["results"][0]["doc_id"] == "mock_001"
        assert "latency_ms" in data
        assert "alpha" in data

    def test_search_result_has_all_fields(self, client: TestClient) -> None:
        resp = client.post("/search", json={"query": "test"})
        result = resp.json()["results"][0]
        # Match your actual API response structure
        required = {"doc_id", "title", "snippet", "hybrid_score"} 
        assert required.issubset(set(result.keys()))

    def test_search_empty_query(self, client: TestClient) -> None:
        resp = client.post("/search", json={"query": ""})
        assert resp.status_code == 422

    def test_search_alpha_out_of_range(self, client: TestClient) -> None:
        resp = client.post("/search", json={"query": "fox", "alpha": 2.0})
        assert resp.status_code == 422

    def test_search_invalid_normalization(self, client: TestClient) -> None:
        resp = client.post(
            "/search", json={"query": "fox", "normalization": "bogus"}
        )
        assert resp.status_code == 422

    def test_search_top_k_out_of_range(self, client: TestClient) -> None:
        resp = client.post("/search", json={"query": "fox", "top_k": 0})
        assert resp.status_code == 422


# ── Feedback ─────────────────────────────────────────────────────────────────

class TestFeedback:
    def test_feedback_endpoint(self, client: TestClient) -> None:
        resp = client.post(
            "/feedback",
            json={"query": "fox", "doc_id": "d1", "relevance": 1},
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ── Metrics ──────────────────────────────────────────────────────────────────

class TestMetrics:
    def test_metrics_endpoint(self, client: TestClient) -> None:
        # Fire a search first so there's data
        client.post("/search", json={"query": "test"})

        resp = client.get("/metrics")
        assert resp.status_code == 200
        text = resp.text
        assert "search_requests_total" in text
        assert "search_latency_p50" in text
        assert "search_latency_p95" in text
