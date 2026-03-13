# Knowledge Search + KPI Dashboard
Enterprise-grade semantic discovery engine with real-time performance analytics and hybrid search intelligence.

## Architecture Overview
The system follows a modern decoupled architecture, combining keyword-based BM25 search with vector embeddings (FAISS) for high-accuracy discovery.

```text
  ┌──────────────┐      ┌──────────────┐      ┌────────────────────────┐
  │   Frontend   │ <──> │   FastAPI    │ <──> │  Search Engine Layers  │
  │   (React)    │      │   Backend    │      │ (BM25 + FAISS + Embed) │
  └──────────────┘      └──────┬───────┘      └────────────────────────┘
                               │
                        ┌──────▼───────┐
                        │    SQLite    │
                        │ (Logs & KPI) │
                        └──────────────┘
```

The **Frontend** (Vite/React) communicates with a **FastAPI** backend that orchestrates the **BM25** (lexical) and **Vector** (semantic) indexes. Operational telemetry and user feedback are persisted in **SQLite**.

## 1-Minute Quickstart
```bash
git clone <repo-url>
cd knowledge-search-project
./up.sh
```
Once the services start, the dashboard will be available at:
**Frontend**: [http://localhost:5173](http://localhost:5173)

## Tech Stack
- **Backend**: Python 3.11+, FastAPI 0.115.0, Uvicorn 0.30.0
- **Search**: Rank-BM25 0.2.2, FAISS-CPU 1.8.0, Sentence-Transformers 3.0.0
- **Database**: SQLite (built-in Python `sqlite3`)
- **Frontend**: React 18, Vite 5.1, Tailwind CSS 3.4, Recharts 2.12
- **Testing**: Pytest 8.3.0

## How to Run Tests
```bash
source .venv/bin/activate
cd backend
python -m pytest tests/ -v
```

## How to Run Evaluation
Quantitative benchmarking using the evaluation harness:
```bash
cd backend
python -m app.eval --queries ../data/eval/queries.jsonl --qrels ../data/eval/qrels.json --alpha 0.5
```

## API Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/search` | Hybrid BM25 + Vector search |
| `POST` | `/feedback` | Record user relevance feedback |
| `GET` | `/health` | System health check and uptime |
| `GET` | `/metrics` | Prometheus-style technical metrics |
| `GET` | `/api/kpi/latency` | p50/p95 search latency statistics |
| `GET` | `/api/kpi/volume` | Query volume over time (last 24h) |
| `GET` | `/api/eval/experiments` | History of evaluation runs |
| `GET` | `/api/logs` | Structured diagnostic logs |

## Project Structure
```text
.
├── backend/
│   ├── app/                # Core FastAPI application
│   │   ├── api/            # Route handlers and middleware
│   │   ├── db/             # Database models and migrations
│   │   ├── search/         # BM25, Vector, and Hybrid logic
│   │   └── utils/          # Preprocessing and metrics
│   └── tests/              # Comprehensive test suite
├── frontend/
│   ├── src/
│   │   ├── components/     # UI building blocks
│   │   ├── pages/          # Dashboard views (Search, KPI, Eval)
│   │   └── api.js          # API service layer
│   └── tailwind.config.js
├── data/
│   ├── raw/                # Original Gutenberg books
│   ├── processed/          # Cleaned JSONL chunks
│   ├── index/              # Persisted FAISS and BM25 indexes
│   └── eval/               # Queries and Qrels ground truth
├── scripts/                # Data download and evaluation generation
├── up.sh                   # Orchestration setup script
└── down.sh                 # Graceful shutdown script
```

## Design Decisions
Technical rationale, trade-offs, and architectural choices are documented in [docs/decision_log.md](docs/decision_log.md).

## SQLite Schema
The system uses SQLite for lightweight, reliable telemetry storage:
- `query_logs`: Stores request performance, counts, and errors.
- `feedback`: Persists user relevance signals for future index tuning.
- `schema_version`: Manages automatic database migrations.
Detailed ER diagrams can be found in [docs/architecture.md](docs/architecture.md).

## Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **Disk Space**: ~2GB (primarily for Sentence Transformer model storage)
- **Memory**: 4GB+ recommended for vector indexing
