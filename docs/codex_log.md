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

## [2026-03-13] Step 05: BM25 Search Implementation
**Prompt:** "Create backend/app/search/bm25.py — implement BM25Index using rank-bm25 with build, query, save, load, and get_all_scores methods."
**Status:** Injected BM25 logic to handle lexical search and persisted the index for faster subsequent loads.

## [2026-03-13] Step 05: BM25 Testing & Verification
**Prompt:** "Create backend/tests/test_bm25.py with pytest tests for BM25Index... [full prompt text]"
**Status:** 13/13 tests passed. [cite_start]Verified ranking, top_k limits, persistence, and edge case handling.