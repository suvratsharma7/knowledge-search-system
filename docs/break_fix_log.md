# Break-Fix Log: Knowledge Search

## Scenario A: Semantic Index Mismatch
**Date:** 2026-03-14
**Type:** Configuration Drift / Data Integrity

### Injection
Manually modified `data/index/vector/metadata.json`:
- `dimension`: 384 → 768
- `model_name`: "all-MiniLM-L6-v2" → "all-mpnet-base-v2"

### Observed Failure
The system previously loaded silently but would crash during inference. After applying the fix, the backend caught the mismatch during startup:
`❌ Error loading indices: Index mismatch: index was built with model='all-mpnet-base-v2' (dim=768) but config expects model='all-MiniLM-L6-v2' (dim=384).`

### Root Cause
The `VectorIndex.load()` method lacked a validation layer to compare the persisted index metadata against the active application configuration (`MODEL_NAME`).

### Fix Applied
1. Updated `app/config.py` to include a centralized `MODEL_NAME` constant.
2. Enhanced `VectorIndex.load()` in `backend/app/search/vector.py` with strict equality checks for `model_name` and `dimension`.
3. Added a `try-except` block in `backend/app/__main__.py` to catch `ValueError` during the searcher initialization.

### Verification
1. Reverted `metadata.json` to correct values → System starts successfully.
2. Injected mismatch again → System catches error and provides rebuild instructions.