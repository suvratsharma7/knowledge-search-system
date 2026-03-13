## [2026-03-13] Step 01: Project Configuration
**Prompt:** "Create backend/app/config.py to define project paths for raw data, processed data, and indices using pathlib. Use constants like DATA_RAW, DATA_PROCESSED, and DATA_INDEX."
[cite_start]**Status:** Established centralized path management to avoid hard-coded absolute paths[cite: 17].

## [2026-03-13] Step 02: Preprocessing Utilities
**Prompt:** "In backend/app/utils/preprocessing.py, implement clean_text (remove extra whitespace/special chars) and tokenize (lowercase, word tokens) functions."
[cite_start]**Status:** Implemented basic text normalization as required by the ingestion pipeline[cite: 44].

## [2026-03-13] Step 03: Data Acquisition
**Prompt:** "Create a script to download a public domain corpus (minimum 300 docs) and chunk them into individual .txt files in data/raw."
[cite_start]**Status:** Successfully acquired and chunked 1,602 documents from Project Gutenberg, satisfying the 300-doc minimum[cite: 41].

## [2026-03-13] Step 04: Data Ingestion Pipeline
**Prompt:** "Create backend/app/ingest.py to scan data/raw, normalize files into JSONL (doc_id, title, text, source, created_at), and save to data/processed/docs.jsonl."
[cite_start]**Status:** Verified ingestion of 1,602 documents into structured JSONL format[cite: 42, 43].

## [2026-03-13] Step 05a: BM25 Search Implementation
**Prompt:** "Create backend/app/search/bm25.py — implement BM25Index using rank-bm25 with build, query, save, load, and get_all_scores methods."
**Status:** Injected BM25 logic to handle lexical search and persisted the index for faster subsequent loads.

## [2026-03-13] Step 05b: BM25 Testing & Verification
**Prompt:** "Create backend/tests/test_bm25.py with pytest tests for BM25Index... [full prompt text]"
**Status:** 13/13 tests passed. [cite_start]Verified ranking, top_k limits, persistence, and edge case handling.

## [2026-03-13] Step 06a: Semantic Vector Indexing
**Prompt:** "In backend/app/search/vector.py, implement a semantic search index using sentence-transformers (all-MiniLM-L6-v2) and FAISS (CPU). Include build, query, save, load, and get_all_scores methods."
**Status:** Initializing dense retrieval. This allows the system to find documents based on meaning rather than just keyword overlap.

## [2026-03-13] Step 06b: Semantic Vector Search
**Prompt:** "Create backend/app/search/vector.py (FAISS + SentenceTransformers) and backend/tests/test_vector.py with dimension validation."
**Status:** 10/10 tests passed. Confirmed semantic ranking (AI queries) and robust metadata validation.

## [2026-03-13] Step 07a: Score Normalization Utilities
**Prompt:** "Create backend/app/search/normalizers.py for Min-Max and Z-score normalization."
**Status:** Decoupling score scaling logic to ensure fair weighting in hybrid search.

## [2026-03-13] Step 07b: Score Normalization Verification
**Prompt:** "Create backend/tests/test_normalizers.py with pytest tests for minmax, zscore, and registry logic."
**Status:** All tests passed. Confirmed robust handling of edge cases like zero-variance scores and empty dictionaries.

## [2026-03-13] Step 07c: Hybrid Search Implementation
**Prompt:** "Create backend/app/search/hybrid.py to implement the HybridSearcher class. It must orchestrate BM25 and Vector indices, applying weighted fusion (alpha) to normalized scores."
**Status:** Integrated lexical and semantic retrieval into a unified HybridSearcher, completing the core retrieval engine.

## [2026-03-13] Step 08: Hybrid Search Orchestrator
**Prompt:** "Create backend/app/search/hybrid.py — implement HybridSearcher to fuse BM25 and Vector results with snippet extraction."
**Status:** Finalizing the core retrieval engine. This component bridges keyword precision and semantic depth.

## [2026-03-13] Step 09: Indexing CLI implementation
**Prompt:** "Create backend/app/index.py — the indexing CLI. Runnable as: python -m app.index --input data/processed/docs.jsonl..."
**Status:** Building the production-grade indexing pipeline to process 1,602 documents into BM25 and Vector indices.

## [2026-03-13] Step 10: Telemetry & Database Setup
**Prompt:** "Create backend/app/db/database.py — SQLite database management for query logging, feedback, and KPI tracking."
**Status:** Implementing system observability. This enables performance monitoring (latency, volume) and user feedback loops.

## [2026-03-13] Step 11: Schema Migration System
**Prompt:** "Create backend/app/db/migrations.py to manage database schema versions and add the 'normalization' column to query_logs."
**Status:** Successfully implemented a migration pipeline. Verified that the database schema can evolve without data loss. 7/7 database tests passed.

## [2026-03-13] Step 12: Production API & Modular Routing
**Prompt:** "Create modular FastAPI routers (Search, KPI, Eval, Logs) with Middleware for Rate Limiting and Request-ID tracking."
**Status:** In Progress. Transitioning to a production-grade service architecture with structured logging and Prometheus-style metrics.

## [2026-03-13] Step 13: Evaluation Data Generation
**Prompt:** "Create scripts/create_eval_data.py to generate queries.jsonl and qrels.json. The script must read real doc_ids from data/processed/docs.jsonl, define 25 diverse queries covering characters, themes, and scenes from the Project Gutenberg corpus, and use keyword matching to assign relevance grades (grade 2 for >= 3 matches, grade 1 for >= 1 match). Ensure qrels.json maps query_ids to doc_ids with these grades, providing 3–10 relevant docs per query."
[cite_start]**Status:** Successfully generated the ground-truth evaluation set[cite: 65, 886]. [cite_start]Verified that queries and relevance labels are mapped to actual document identifiers, enabling rigorous performance testing[cite: 883].

## [2026-03-13] Step 14: Evaluation Harness & Hyperparameter Tuning
**Prompt:** "Create backend/app/eval.py to implement the evaluation harness. Requirements: Load queries/qrels, run hybrid search with configurable alpha/normalization, and compute nDCG@10, Recall@10, and MRR@10 from scratch. Execute a 5-run experimental sweep across alpha values [0.0, 0.2, 0.5, 0.8, 1.0] to identify the optimal retrieval balance."
**Status:** Completed the evaluation pipeline and identified Alpha=0.8 as the optimal configuration (nDCG@10: 0.3773). Results mathematically prove that a lexical-heavy hybrid approach outperforms standalone BM25 or Vector search for this corpus.

## [2026-03-13] Step 15: Frontend Project Initialization
**Prompt:** "Initialize a React + Vite frontend with TypeScript, Tailwind CSS, Recharts, and React Query. Configure API proxying and core fetch wrappers for search, telemetry, and evaluation endpoints."
**Status:** Frontend infrastructure established. Environment is prepared for dashboard development and integration with the existing FastAPI service.

## [2026-03-13] Step 16: App Shell & Navigation Implementation
**Prompt:** "Create frontend/src/App.jsx with react-router-dom, a professional navigation bar, and 4 tabs (Search, KPI, Eval, Debug). Include an API health indicator."
**Status:** App shell is functional. Navigation and routing are established using a layout-first approach. Integrated a live health check to monitor backend connectivity directly from the UI.

## [2026-03-13] Step 17: Search UI Implementation
**Prompt:** "Create SearchPage.jsx with dynamic controls for alpha, top_k, and normalization. Display results with score visualizations (BM25 vs Vector) and integrated latency tracking."
**Status:** Search interface is live. Users can now manipulate hybrid search parameters in real-time and visualize the score composition of each result. Successfully integrated the searchDocs API wrapper.

## [2026-03-13] Step 18: KPI Dashboard Implementation
**Prompt:** "Create KPIPage.jsx with latency panels (p50/p95), hourly request volume line charts, and query frequency tables."
**Status:** Performance monitoring is live. Integrated Recharts for data visualization and implemented an auto-refresh mechanism (30s interval) to keep telemetry data current.

## [2026-03-13] Step 19: Evaluation & Debugging Hub
**Prompt:** "Create EvalPage.jsx with experiment tables and nDCG trend charts. Create DebugPage.jsx with filtered log tables and auto-refresh capabilities."
**Status:** Dashboard completed. Integrated nDCG tracking to visualize Alpha parameter performance over time. Debug logs allow for granular inspection of API request life cycles and error states. Frontend Phase 3 is finalized.

## [2026-03-14] Step 20: Orchestration & Automation Scripts
**Prompt:** "Create up.sh and down.sh in the repository root to handle venv creation, dependency installation, and parallel service launch for backend and frontend. Implement port-specific process termination for 8000 and 5173."
**Status:** Completed automation layer. Unified the development lifecycle into a single-command setup. Verified cross-platform compatibility for Python/Node orchestration and implemented atomic service shutdowns.

## [2026-03-14] Step 21: Environment Stability & Git Hygiene
**Prompt:** "Create requirements.txt with pinned versions (FastAPI, Uvicorn, FAISS, etc.) and a comprehensive .gitignore to exclude virtual environments, node_modules, local data directories, and cache files."
**Status:** Completed. Hardened the project for portability by pinning dependencies and ensuring local artifacts/data indices are not tracked in version control.

## [2026-03-14] Step 22: Documentation & Portfolio Finalization
**Prompt:** "Create a professional README.md with architecture diagrams, quickstart instructions, tech stack details, and API documentation to serve as the project landing page."
**Status:** Completed. Project is now recruiter-ready with comprehensive documentation covering the hybrid search architecture, evaluation benchmarks, and automated deployment steps.

## [2026-03-14] Step 23: Break-Fix A — Semantic Index Mismatch
**Prompt:** "Implement startup validation in VectorIndex.load() to check metadata against config. If dimension or model name mismatch, raise a clear ValueError with rebuild instructions. Catch this in FastAPI startup to prevent silent failures."
**Status:** Completed. Injected defensive validation logic. Verified that changing metadata.json now triggers a descriptive ValueError instead of a silent load.

## [2026-03-14] Step 24: Break-Fix B — Schema Migration & Data Integrity
**Prompt:** "Refactor migrations.py to support both a versioned registry and a dynamic self-healing check for the user_agent column. Fix the type mismatch between string paths and sqlite3 connections and ensure row_factory is set for dictionary access."
**Status:** Completed. Verified that the backend successfully performs a 'Double Migration' (Registry + Self-Healing). The system now auto-repairs schema drift on startup, ensuring zero data loss and persistent logging resilience.

## [2026-03-14] Step 25: Break-Fix C — Numerical Instability Regression
**Prompt:** "Fix divide-by-zero bug in minmax_normalize. Restore epsilon safeguards and identical-score early returns. Implement unit tests to verify stability with identical and near-identical score distributions."
**Status:** Completed. Hardened the normalization layer against floating-point errors. Verified metrics recovery via evaluation harness and confirmed that new unit tests catch edge cases that previously caused NaN results.

## [2026-03-14] Step 26: System Architecture & Defensive Design Documentation
**Prompt:** "Create a comprehensive architecture.md that outlines the system components, data flow, and mathematical foundations. Ensure the documentation highlights the defensive engineering wins from the Break-Fix scenarios (Schema migrations, model validation, and numerical stability)."
**Status:** Completed. Authored a high-level technical document bridging the gap between raw code and system design. Integrated ASCII diagrams, updated SQLite schemas including the 'user_agent' migration, and documented the epsilon-stabilized normalization logic for external review.

## [2026-03-14] Step 27: Engineering Decision Log
**Prompt:** "Document the technical trade-offs of the project in a decision_log.md. Justify choices like SQLite, FAISS, and MiniLM in the context of CPU-only constraints and minimal setup time."
**Status:** Completed. Authored a strategic document detailing the 'Why' behind the tech stack. This provides clear rationale for recruiters on why lightweight, local-first libraries were prioritized over enterprise-heavy alternatives like Elasticsearch or PostgreSQL.