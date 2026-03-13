# Architecture Documentation - Knowledge Search Platform

## 1. System Overview
The Knowledge Search Platform is a production-ready discovery engine that bridges the gap between keyword-based retrieval and semantic understanding.

```text
  ┌─────────────────────────────────────────────────────────────┐
  │                        User Browser                         │
  │    (React Dashboard: Search, KPI, Eval, Debug Views)        │
  └─────────────┬───────────────────────────────▲───────────────┘
                │ HTTP / JSON                   │
  ┌─────────────▼───────────────────────────────┴───────────────┐
  │                      FastAPI Backend                        │
  │  (Orchestration, API Routing, Logic, Normalization)        │
  └─────────────┬───────────────┬───────────────┬───────────────┘
                │               │               │
  ┌─────────────▼───────┐ ┌─────▼─────────┐ ┌───▼───────────────┐
  │    Search Layers    │ │ Resilience &  │ │ Storage & Telemetry │
  │ (BM25 + FAISS Vec)  │ │ Break-Fix Ops │ │ (SQLite + Local FS) │
  └─────────────────────┘ └───────────────┘ └───────────────────┘
```

## 2. Component Descriptions

### Ingestion Pipeline
- **Duty**: Prepares raw Gutenberg text for efficient indexing.
- **Process**: Handles "Project Gutenberg" boilerplate removal, tokenizes text, and creates overlapping 500-token chunks to maintain context at boundaries.
- **Output**: `data/processed/docs.jsonl`.

### BM25 Indexing (Lexical Search)
- **Duty**: Provides exact keyword matching.
- **Technology**: `rank-bm25`.
- **Strength**: High precision for proper nouns, years, and specific terminology (e.g., "Sherlock", "1887").

### Vector Indexing (Semantic Search)
- **Duty**: Captures conceptual similarity.
- **Technology**: `sentence-transformers` (`all-MiniLM-L6-v2`) + `FAISS`.
- **Strength**: Handles synonyms and context (e.g., matching "detective" when searching for "investigator").

### Hybrid Search Combiner
- **Duty**: Merges divergent score scales into a unified ranking.
- **Logic**: Normalizes lexical and semantic scores, then computes a weighted average based on the `alpha` parameter.

### FastAPI API Layer
- **Duty**: Service delivery, request validation, and asynchronous telemetry logging.
- **Middleware**: Includes CORS handling and simple in-memory rate limiting.

### SQLite Persistence
- **Duty**: Persistent operational telemetry and feedback storage.
- **System**: WAL (Write-Ahead Logging) enabled for high concurrency during dashboard updates.

### React Dashboard
- **Duty**: Real-time visualization of performance (Recharts), search experimentation, and diagnostic log viewing.

## 3. Data Flow Diagram
```text
[User Search Request]
       │
       ▼
[FastAPI: POST /search] ───► [Middleware: Rate Limit Check]
       │
       ├─► [Parallel Retrieval: BM25 + FAISS]
       │
       ├─► [Normalization: Min-Max / Z-Score] ◄── [ Safeguard: Div-by-Zero Check ]
       │
       ├─► [Rank Merger: (1-alpha)*Vec + alpha*BM25]
       │
       ├─► [Telemetry: Async Log to SQLite] ◄─── [ Safeguard: Operational Repair ]
       │
       ▼
[JSON Search Response]
```

## 4. SQLite Schema
```sql
-- Main telemetry for search performance
CREATE TABLE query_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id   TEXT    NOT NULL,
    query        TEXT    NOT NULL,
    latency_ms   REAL    NOT NULL,
    top_k        INTEGER NOT NULL,
    alpha        REAL    NOT NULL,
    result_count INTEGER NOT NULL,
    error        TEXT,
    timestamp    TEXT    NOT NULL DEFAULT (datetime('now')),
    normalization TEXT    DEFAULT 'minmax',
    user_agent   TEXT    NOT NULL DEFAULT ''
);

-- User feedback for evaluation tuning
CREATE TABLE feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    query      TEXT    NOT NULL,
    doc_id     TEXT    NOT NULL,
    relevance  INTEGER NOT NULL,
    timestamp  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Version tracking for robust migrations
CREATE TABLE schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

## 5. API Contract Summary

| Endpoint | Method | Request Shape | Response Shape |
| :--- | :--- | :--- | :--- |
| `/search` | `POST` | `{query, top_k, alpha, normalization}` | `{results: [], latency_ms: 0.0, ...}` |
| `/feedback` | `POST` | `{query, doc_id, relevance}` | `{"status": "ok"}` |
| `/api/kpi/latency` | `GET` | *None* | `{"p50_latency": 0.0, "p95_latency": 0.0}` |
| `/api/logs` | `GET` | `?limit=50&severity=error` | `[ {request_id, query, ...}, ... ]` |

## 6. Normalization Strategies

### Min-Max Scaling
`norm = (score - min_val) / (max_val - min_val + epsilon)`
- **Epsilon**: `1e-10` to prevent division by zero.
- **Behavior**: If `max == min`, all scores transform to `0.0`.

### Z-Score (Standardization)
`z = (score - mean) / (std_dev + epsilon)`
- **Standardization**: Centers distribution at 0 and scales by population standard deviation.

## 7. Evaluation Methodology

### nDCG@10 (Normalized Discounted Cumulative Gain)
`DCG@k = sum( (2^rel_i - 1) / log2(i + 1) )`
- Measures ranking quality; rewards placing relevant items at the top.

### Recall@10
`Recall = (Relevant retrieved in Top 10) / (All relevant in test set)`

### MRR (Mean Reciprocal Rank)
`MRR = 1 / first_relevant_rank`

## 8. Security & Resilience

### Security Considerations
- **Rate Limiting**: Simple sliding window (60 req/min/IP) in `routes.py`.
- **Validation**: Strict Pydantic models for all inbound JSON payloads.

### Resilience Features (The "Break-Fix" Suite)
The platform includes built-in recovery for common operational failures:
- **Index Startup Validation**: The server validates the FAISS index dimension vs. the current embedding model. Misaligned indexes trigger a clear warning or an **automatic rebuild** via the `--auto-rebuild` flag.
- **Robust Migrations**: If the database schema is manually altered (e.g., a `NOT NULL` column added without a default), the migration engine performs a **safe table recreation** (Copy-Drop-Rename) to restore operational state.
- **Fault-Tolerant Logging**: Database logging is wrapped in defensive `try-except` blocks. Telemetry failures will not crash the search service, ensuring maximum uptime.
- **Numerical Stability**: Normalization algorithms use epsilon offsets and early-exit checks to remain stable even with identical or single-result score sets.
