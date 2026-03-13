import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 1. Path setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import backend.app.db.database as db_mod

@pytest.fixture()
def client(tmp_path: Path):
    """TestClient that bypasses all startup events and mocks the engine."""
    # Patch the DB Path so we don't touch real logs
    with patch.object(db_mod, "DB_PATH", tmp_path / "test.db"):
        
        # STOP the real engine from ever loading
        with patch("backend.app.search.bm25.BM25Index.load"), \
             patch("backend.app.search.vector.VectorIndex.load"), \
             patch("backend.app.__main__.HybridSearcher"):
            
            # Import the actual app instance
            from backend.app.__main__ import app
            
            # CLEAR existing startup handlers so they don't crash our test
            app.router.on_startup = [] 
            
            # Initialize temp DB
            db_mod.init_db()

            # Create the Mock Searcher
            mock_searcher = MagicMock()
            mock_searcher.search.return_value = [{
                "doc_id": "mock_001",
                "title": "Mock Document",
                "snippet": "test snippet",
                "hybrid_score": 0.95
            }]
            
            # Inject mock into app state BEFORE the client starts
            app.state.searcher = mock_searcher

            with TestClient(app) as tc:
                yield tc