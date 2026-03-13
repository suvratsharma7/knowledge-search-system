# Design Decision Log - Knowledge Search Platform

This document outlines the key architectural decisions made during the development of the Knowledge Search platform, justified against the project's core constraints.

## Decision Matrix

| Decision | Options Considered | Choice | Rationale |
| :--- | :--- | :--- | :--- |
| **Embedding Model** | `all-MiniLM-L6-v2`, `all-mpnet-base-v2`, `e5-small` | **`all-MiniLM-L6-v2`** | Selected for its optimal performance-to-size ratio on **CPU-only** environments. It provides high-quality 384-dim embeddings while maintaining a small disk footprint (~80MB), ensuring the < 30 min setup target. |
| **Vector Index** | `FAISS IndexFlatIP`, `hnswlib`, `Annoy` | **`FAISS IndexFlatIP`** | `FAISS` is the industry standard for vector similarity. `IndexFlatIP` (Inner Product) on L2-normalized vectors provides exact cosine similarity without the memory overhead or build-time complexity of HNSW, perfectly suited for a single-server **minimal dependency** deployment. |
| **BM25 Library** | `rank-bm25`, `Elasticsearch`, `Whoosh` | **`rank-bm25`** | `rank-bm25` is a lightweight, pure-Python implementation. Unlike Elasticsearch, it requires no external service or complex JVM setup, allowing the system to launch via a **single `up.sh`** without manual infrastructure management. |
| **Normalization** | `MinMax`, `Z-score`, `RRF` | **`MinMax`** | Min-Max scaling is computationally inexpensive and maps search scores to a predictable `[0, 1]` range. This is essential for the **CPU-only** constraint and provides a more intuitive visualization on the dashboard than raw Z-scores. |
| **Database** | `SQLite`, `PostgreSQL`, `just files` | **`SQLite`** | `SQLite` is serverless, zero-config, and included in the Python standard library. It avoids the "external service" requirement of Postgres, ensuring a robust telemetry layer while keeping **minimal dependencies**. |
| **Frontend** | `React+Vite`, `Streamlit`, `Gradio` | **`React+Vite`** | While Streamlit is faster to draft, `React+Vite` allows for a premium, custom UI with rich analytics (Recharts) and structured debug views. This delivers a **WOW-factor** experience while staying within the single-command launch model. |
| **Scoring Combination** | `Linear Interpolation`, `RRF`, `Learned Weights` | **`Linear Interpolation`** | Linear interpolation (the `alpha` parameter) allows users to dynamically balance lexical vs. semantic results. It is simpler and faster at runtime for **CPU environments** compared to multi-pass fusion or learned ranking models. |
| **Text Preprocessing** | `Custom Tokenizer`, `NLTK`, `spaCy` | **`Custom Tokenizer`** | A regex-based custom tokenizer was chosen to avoid the multi-gigabyte downloads and setup complexities of NLTK or spaCy models, ensuring the whole project stays under the **30 min setup time** limit. |

## Architectural Constraints Compliance

- **CPU-only**: All chosen libraries (`rank-bm25`, `faiss-cpu`, `sentence-transformers`) are optimized for CPU execution without requiring CUDA.
- **Single `up.sh`**: By avoiding external databases (Oracle/Postgres) or search engines (Elastic/Solr), the entire stack can be launched with one script.
- **Minimal Dependencies**: We prioritized libraries that are either pure-Python or have standardized wheels (`faiss-cpu`), avoiding complex system-level compile steps.
- **Setup Speed**: Large model downloads (Gradio/spaCy) were avoided to ensure the first-run experience remains rapid and predictable.
