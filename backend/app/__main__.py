import uvicorn
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Imports for your modular routers
from app.api.routes import router as search_router
from app.api.kpi_routes import router as kpi_router
from app.api.eval_routes import router as eval_router
from app.api.log_routes import router as log_router
from app.api.middleware import RequestLoggingMiddleware

# 2. Search Engine Core Imports
from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex
from app.search.hybrid import HybridSearcher
from app.config import BM25_INDEX_DIR, VECTOR_INDEX_DIR, DATA_INDEX

app = FastAPI(title="Knowledge Search System")

# 3. Add Middlewares (Order matters: Logging first, then CORS)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your React app to talk to this API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Include All Modular Routers
app.include_router(search_router) # The main /search and /feedback
app.include_router(kpi_router)    # /api/kpi
app.include_router(eval_router)   # /api/eval
app.include_router(log_router)    # /api/logs

# 5. Your existing Startup Logic
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing Search Engine...")
    try:
        bm25 = BM25Index.load(BM25_INDEX_DIR)
        vector = VectorIndex.load(VECTOR_INDEX_DIR)
        
        with open(DATA_INDEX / "doc_store.json", "r", encoding="utf-8") as f:
            doc_store = json.load(f)
            
        # Attach searcher to app state so routes can find it
        app.state.searcher = HybridSearcher(bm25, vector, doc_store)
        print("✅ HybridSearcher ready with indices loaded.")
        print("📊 Analytics and Log routes active.")
    except Exception as e:
        print(f"❌ Error loading indices: {e}")
        app.state.searcher = None

if __name__ == "__main__":
    # Use the string import for reload to work correctly
    uvicorn.run("app.__main__:app", host="0.0.0.0", port=8000, reload=True)