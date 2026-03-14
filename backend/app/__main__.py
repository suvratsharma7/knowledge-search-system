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

# 2. Search Engine Core & DB Imports
from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex
from app.search.hybrid import HybridSearcher
from app.db.database import init_db           # Ensure tables exist
from app.db.migrations import run_migrations   # The self-healing logic
from app.config import BM25_INDEX_DIR, VECTOR_INDEX_DIR, DATA_INDEX, DB_PATH

app = FastAPI(title="Knowledge Search System")

# 3. Add Middlewares
# CRITICAL: We explicitly list the frontend port in case "*" is being flaky
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
app.add_middleware(RequestLoggingMiddleware)

# 4. Include All Modular Routers
app.include_router(search_router)
app.include_router(kpi_router)
app.include_router(eval_router)
app.include_router(log_router)

# Added a root health check so http://localhost:8000 doesn't show "Not Found"
@app.get("/")
async def root():
    return {"status": "online", "message": "Knowledge Search API is reaching for the stars"}

# 5. Startup Logic with Self-Healing Migrations
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing Search Engine...")
    
    # --- DATABASE SELF-HEALING ---
    try:
        init_db()  # Ensure basic tables exist
        print("🛠️ Verifying database schema integrity...")
        run_migrations(str(DB_PATH)) 
    except Exception as db_err:
        print(f"⚠️ Database initialization/migration warning: {db_err}")

    try:
        bm25 = BM25Index.load(BM25_INDEX_DIR)
        vector = VectorIndex.load(VECTOR_INDEX_DIR)
        
        with open(DATA_INDEX / "doc_store.json", "r", encoding="utf-8") as f:
            doc_store = json.load(f)
            
        app.state.searcher = HybridSearcher(bm25, vector, doc_store)
        print("✅ HybridSearcher ready with indices loaded.")
    except Exception as e:
        print(f"❌ Error loading indices: {e}")
        app.state.searcher = None

if __name__ == "__main__":
    # Using the module string "app.__main__:app" allows the reloader to work properly
    uvicorn.run("app.__main__:app", host="0.0.0.0", port=8000, reload=True)
    